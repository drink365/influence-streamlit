# pages/Login.py
# 顧問登入（Email OTP）
# - 讀取 ADVISORS 白名單（secrets.toml）
# - SMTP 可選；未設時會在畫面顯示「測試用 OTP」
# - OTP 節流與錯碼鎖定
# - 成功後記入 session_state 並 rerun（相容不同 Streamlit 版本）

import time
import random
from datetime import datetime, timedelta
import streamlit as st

# ===================== 基本設定 =====================
st.set_page_config(page_title="顧問登入（Email OTP）", page_icon="🔒", layout="centered")
st.title("🔐 顧問登入（Email OTP）")
st.caption("輸入公司白名單 Email。我們會寄送 6 位數驗證碼。若未設定 SMTP，會顯示測試用驗證碼。")

# --------- 小工具 ---------
def _now() -> float:
    return time.time()

def _rerun():
    # 兼容新舊版 Streamlit
    if hasattr(st, "rerun"):
        st.rerun()
    else:
        st.experimental_rerun()

def _normalize_email(e: str) -> str:
    return (e or "").strip().lower()

def _get_advisors():
    # secrets.toml:
    # [ADVISORS]
    # "grace@example.com" = "Grace|admin"
    # "advisor1@example.com" = "顧問A|user"
    tbl = st.secrets.get("ADVISORS", {})
    # 轉小寫 key
    return {k.strip().lower(): v for k, v in dict(tbl).items()}

def _parse_display_and_role(val: str):
    # "顯示名|角色"
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
    role = "admin" if role == "admin" else "user"
    return {"name": name or email, "role": role}

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
st.session_state.setdefault("otp_expires_at", 0.0)  # epoch 秒
st.session_state.setdefault("otp_attempts", 0)
st.session_state.setdefault("otp_lock_until", 0.0)  # epoch 秒

# 登入成功旗標（避免無限 rerun）
st.session_state.setdefault("__just_logged_in__", False)

# 已登入的話顯示身份
if st.session_state.get("auth_ok"):
    who = st.session_state.get("advisor_name", "—")
    role = st.session_state.get("advisor_role", "user")
    st.success(f"目前登入：{who}｜角色：{role}")

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
    # 錯誤：不在白名單
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
            st.session_state["otp_expires_at"] = (_now() + 600)  # 10 分鐘有效
            st.session_state["otp_attempts"] = 0  # 重置嘗試次數

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
    # 節流／鎖定檢查
    if _now() < st.session_state["otp_lock_until"]:
        wait_s = int(st.session_state["otp_lock_until"] - _now())
        st.error(f"嘗試次數過多，請 {wait_s} 秒後再試。")
    elif not email_norm or email_norm != st.session_state.get("otp_email"):
        st.error("請先輸入 Email 並點『寄送驗證碼』。")
    else:
        # 檢查 OTP
        sent = st.session_state.get("otp_code", "")
        expires = st.session_state.get("otp_expires_at", 0.0)

        if not sent:
            st.error("尚未產生驗證碼，請先點『寄送驗證碼』。")
        elif _now() > expires:
            st.error("驗證碼已過期，請重新取得。")
        elif code_input.strip() != sent:
            # 記錄錯誤次數；連續 5 次錯誤鎖 10 分鐘
            st.session_state["otp_attempts"] += 1
            remain = max(0, 5 - st.session_state["otp_attempts"])
            if remain == 0:
                st.session_state["otp_lock_until"] = _now() + 600  # 10 分鐘
                st.error("驗證碼錯誤次數過多，已鎖定 10 分鐘。")
            else:
                st.error(f"驗證碼錯誤，請再試。尚可再試 {remain} 次。")
        else:
            # 驗證成功 → 設定登入狀態
            wl = _is_whitelisted(email_norm)
            if not wl:
                st.error("此 Email 未在顧問白名單中。")
            else:
                st.session_state["auth_ok"] = True
                st.session_state["advisor_id"] = email_norm
                st.session_state["advisor_name"] = wl["name"]
                st.session_state["advisor_role"] = wl["role"]
                st.session_state["__just_logged_in__"] = True

                st.success(f"登入成功：{wl['name']}｜角色：{wl['role']}")
                _rerun()

# 避免無限 rerun
if st.session_state.get("__just_logged_in__"):
    st.session_state["__just_logged_in__"] = False
