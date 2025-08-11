from __future__ import annotations
from typing import Optional, Tuple
import random, time
import streamlit as st

# ============ SMTP ============
import smtplib
from email.message import EmailMessage

def _smtp_cfg():
    s = st.secrets.get("SMTP", {})
    need = ["HOST","PORT","USER","PASS","FROM"]
    miss = [k for k in need if not s.get(k)]
    if miss: return None
    return s

def _send_mail(to_email: str, subject: str, body: str) -> bool:
    cfg = _smtp_cfg()
    if not cfg: return False
    try:
        msg = EmailMessage(); msg["Subject"] = subject; msg["From"] = cfg["FROM"]; msg["To"] = to_email; msg.set_content(body)
        with smtplib.SMTP(cfg["HOST"], int(cfg["PORT"])) as server:
            server.starttls(); server.login(cfg["USER"], cfg["PASS"]); server.send_message(msg)
        return True
    except Exception:
        return False

# 顧問名單

def _advisors():
    return dict(st.secrets.get("ADVISORS", {}))


def is_whitelisted(email: str) -> bool:
    adv = _advisors(); return email.lower().strip() in {k.lower() for k in adv.keys()}


def resolve_profile(email: str) -> Tuple[str, str]:
    raw = _advisors().get(email) or _advisors().get(email.lower().strip())
    if raw and isinstance(raw, str) and "|" in raw:
        name, role = raw.split("|", 1)
        role = role.strip().lower()
        if role not in ("admin","user"): role = "user"
        return name.strip(), role
    return email, "user"

# OTP 流程 + 節流

def _now() -> int:
    return int(time.time())

LOCK_KEY = "otp_locked_until"
FAIL_KEY = "otp_fail_count"
LAST_ISSUE_KEY = "otp_last_issue"


def issue_otp(email: str) -> str:
    email = email.lower().strip()
    # 被鎖定？
    locked = st.session_state.get(LOCK_KEY, 0)
    if _now() < locked:
        raise RuntimeError("多次錯誤嘗試，請稍後再試。")
    # 節流：60 秒內僅允許一次寄送
    last_issue = st.session_state.get(LAST_ISSUE_KEY, 0)
    if _now() - last_issue < 60:
        raise RuntimeError("驗證碼已寄出，請稍候再試。")

    code = f"{random.randint(0, 999999):06d}"
    st.session_state["otp_email"] = email
    st.session_state["otp_code"] = code
    st.session_state["otp_expiry"] = _now() + 300  # 5 分鐘
    st.session_state[LAST_ISSUE_KEY] = _now()
    sent = _send_mail(email, "您的登入驗證碼", f"您的驗證碼為：{code}（5 分鐘內有效）")
    st.session_state["otp_dev_visible"] = (not sent)
    # 重置錯誤次數
    st.session_state[FAIL_KEY] = 0
    return code


def verify_otp(input_code: str) -> bool:
    code = st.session_state.get("otp_code")
    exp = st.session_state.get("otp_expiry", 0)
    if not code or not input_code or _now() > exp:
        return False
    ok = input_code.strip() == code
    if ok:
        st.session_state[FAIL_KEY] = 0
        return True
    # 累計錯誤
    st.session_state[FAIL_KEY] = int(st.session_state.get(FAIL_KEY, 0)) + 1
    if st.session_state[FAIL_KEY] >= 5:
        st.session_state[LOCK_KEY] = _now() + 600  # 10 分鐘鎖定
    return False


def login(email: str, display_name: str, role: str):
    st.session_state["advisor_email"] = email.lower().strip()
    st.session_state["advisor_name"] = display_name
    st.session_state["advisor_id"] = st.session_state["advisor_email"]
    st.session_state["advisor_role"] = role


def logout():
    for k in ["advisor_email","advisor_name","advisor_id","advisor_role","otp_email","otp_code","otp_expiry","otp_dev_visible",FAIL_KEY,LOCK_KEY,LAST_ISSUE_KEY]:
        st.session_state.pop(k, None)


def is_logged_in() -> bool:
    return bool(st.session_state.get("advisor_id"))


def current_role() -> str:
    return st.session_state.get("advisor_role", "user")
