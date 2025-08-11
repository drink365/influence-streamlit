# pages/Login.py
# 顧問登入（Email OTP）— 已登入自動跳轉
# - 白名單驗證（secrets.ADVISORS）
# - SMTP 可選；未設時顯示測試用 OTP
# - OTP 節流與鎖定
# - 已登入 or 登入成功後：自動跳轉到 POST_LOGIN_PAGE（預設 2_Diagnostic）

import time
import random
from datetime import datetime, timedelta
import streamlit as st

# ===================== 基本設定 =====================
st.set_page_config(page_title="顧問登入（Email OTP）", page_icon="🔒", layout="centered")
st.title("🔐 顧問登入（Email OTP）")
st.caption("輸入公司白名單 Email。我們會寄送 6 位數驗證碼。若未設定 SMTP，會顯示測試用驗證碼。")

# 目標頁可在 secrets 設定：POST_LOGIN_PAGE="pages/2_Diagnostic.py"
TARGET_PAGE = st.secrets.get("POST_LOGIN_PAGE", "pages/2_Diagnostic.py")

# --------- 小工具 ---------
def _now() -> float:
    return time.time()

def _rerun():
    if hasattr(st, "rerun"):
        st.rerun()
    else:
        st.experimental_rerun()

def _goto_target():
    """已登入就跳轉；switch_page 失敗則 rerun；最後給可點連結備援。"""
    # 避免重複跳轉
    if st.session_state.get("__login_redirected__", False):
        return
    st.session_state["__login_redirected__"] = True

    # 優先 switch_page
    try:
        if hasattr(st, "switch_page"):
            st.switch_page(TARGET_PAGE)
            return
    except Exception:
        pass

    # 退一步：rerun（有些部署不支援 switch_page）
    try:
        _rerun()
        return
    except Exception:
        pass

    # 最後備援：給連結
    st.markdown(f"➡️ [前往下一步]({TARGET_PAGE.split('/')[-1].replace('.py','')})")

def _normalize_email(e: str) -> str:
    return (e or "").strip().lower()

def _get_advisors():
    tbl = st.secrets.get("ADVISORS", {})
    return {k.strip().lower(): v for k, v in dict(tbl).items()}

def _parse_display_and_role(val: str):
    if not val:
        return ("", "user")
    parts = [p.strip() for p in str(val).split("|", 1)]
    if len(parts) == 1:
        return (parts[0], "user")
    return (parts[0], parts[1].lower() or "user")

def _is_whitelisted(email: str):
    advisors = _get_advisors()
    val = advisors.get(_normalize_email(email))
    if not val:
        return None
    name, role = _parse_display_and_role(val)
    return {"name": name or email, "role": ("admin" if role == "admin" else "user")}

def _gen_otp() -> str:
    return f"{random.randint(0, 999999):06d}"

def _smtp_enabled() -> bool:
    s = st.secrets.get("SMTP", {})
    return bool(s and s.get("HOST") and s.get("PORT") and s.get("USER") and s.get("PASS") and s.get("FROM"))

def _send_otp_smtp(to_email: str, code: str) -> bool:
    try:
        from email.message import EmailMessage
        import smtplib, ssl

        cfg = st.secrets.get("SMTP", {})
        host = cfg.get("HOST"); port = int(cfg.get("PORT", 587))
        user = cfg.get("USER"); pwd = cfg.get("PASS"); sender = cfg.get("FROM")

        msg = EmailMessage()
        msg["Subject"] = "您的登入驗證碼"
        msg["From"] = sender
        msg["To"] = to_email
        msg.set_content(f"您的登入驗證碼是：{code}\n10 分鐘內有效。")

        context = ssl.create_default_context()
        with smtplib.SMTP(host, port) as server:
            server.starttls(context=context)
            server.login(user, pwd)
            server.send_message(msg)
        return True
    except Exception:
        return False

# --------- Session 狀態欄位初始化 ---------
st.session_state.setdefault("otp_email", "")
st.session_state.setdefault("otp_code", "")
st.session_state.setdefault("otp_expires_at", 0.0)
st.session_state.setdefault("otp_attempts", 0)
st.session_state.setdefault("otp_lock_until", 0.0)
st.session_state.setdefault("__login_redirected__", False)

# ============ 若已登入：立刻跳轉 ============
if st.session_state.get("auth_ok", False):
    st.success(f"目前登入：{st.session_state.get('advisor_name','—')}｜角色：{st.session_state.get('advisor_role','user')}")
    _goto_target()
    st.stop()

# ===================== 表單 =====================
with st.form("login_form"):
    email = st.text_input("公司 Email", value=st.session_state.get("otp_email", ""), placeholder="you@company.com")
    cols = st.columns([1, 1])
    with cols[0]:
        send_req = st.form_submit_button("寄送驗證碼")
    with cols[1]:
        code_input = st.text_input("驗證碼（6 位數）", value="", max_chars=6)
    login_req = st.form_submit_button("登入")

email_norm = _normalize_email(email)

# ===================== 送出驗證碼 =====================
if send_req:
    wl = _is_whitelisted(email_norm)
    if not wl:
        st.error("此 Email 未在顧問白名單中，請聯繫管理員新增。")
    else:
        if _now() < st.session_state["otp_lock_until"]:
            wait_s = int(st.session_state["otp_lock_until"] - _now())
            st.warning(f"嘗試次數過多，請 {wait_s} 秒後再試。")
        else:
            code = _gen_otp()
            st.session_state["otp_email"] = email_norm
            st.session_state["otp_code"] = code
            st.session_state["otp_expires_at"] = (_now() + 600)  # 10 分鐘
            st.session_state["otp_attempts"] = 0

            if _smtp_enabled():
                ok = _send_otp_smtp(email_norm, code)
                if ok:
                    st.info("驗證碼已寄出，請於 10 分鐘內輸入完成登入。")
                else:
                    st.warning("寄送失敗，但您可在下方直接輸入測試用驗證碼。")
                    st.code(code, language="text")
            else:
                st.info("尚未設定 SMTP。以下為測試用驗證碼（上線前請設定 SMTP）：")
                st.code(code, language="text")

# ===================== 登入流程 =====================
if login_req:
    if _now() < st.session_state["otp_lock_until"]:
        wait_s = int(st.session_state["otp_lock_until"] - _now())
        st.error(f"嘗試次數過多，請 {wait_s} 秒後再試。")
    elif not email_norm or email_norm != st.session_state.get("otp_email"):
        st.error("請先輸入 Email 並點『寄送驗證碼』。")
    else:
        sent = st.session_state.get("otp_code", "")
        expires = st.session_state.get("otp_expires_at", 0.0)

        if not sent:
            st.error("尚未產生驗證碼，請先點『寄送驗證碼』。")
        elif _now() > expires:
            st.error("驗證碼已過期，請重新取得。")
        elif (code_input or "").strip() != sent:
            st.session_state["otp_attempts"] += 1
            remain = max(0, 5 - st.session_state["otp_attempts"])
            if remain == 0:
                st.session_state["otp_lock_until"] = _now() + 600
                st.error("驗證碼錯誤次數過多，已鎖定 10 分鐘。")
            else:
                st.error(f"驗證碼錯誤，請再試。尚可再試 {remain} 次。")
        else:
            # ✅ 驗證成功 → 設定登入狀態並跳轉
            wl = _is_whitelisted(email_norm)
            if not wl:
                st.error("此 Email 未在顧問白名單中。")
            else:
                st.session_state["auth_ok"] = True
                st.session_state["advisor_id"] = email_norm
                st.session_state["advisor_name"] = wl["name"]
                st.session_state["advisor_role"] = wl["role"]
                st.success(f"登入成功：{wl['name']}｜角色：{wl['role']}")
                _goto_target()
                st.stop()
