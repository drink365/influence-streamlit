import streamlit as st
from datetime import datetime
from src.repos.booking_repo import BookingRepo
from src.repos.event_repo import EventRepo

import smtplib
from email.message import EmailMessage

st.set_page_config(page_title="預約", page_icon="📅", layout="centered")

# 讀取 Session / Query 的 case_id（新：自動帶入）
prefill = st.session_state.get("incoming_case_id")
q = st.query_params
q_case = q.get("case", "") if isinstance(q.get("case"), str) else (q.get("case")[0] if q.get("case") else "")

st.title("📅 預約顧問")
case_id = st.text_input("案件碼（可選）", value=prefill or q_case or "")
name = st.text_input("姓名/稱呼*")
phone = st.text_input("手機*")
email = st.text_input("Email")
slot = st.selectbox("時段*", ["這週三 下午","這週五 晚上","下週一 上午","自訂（備註）"])
note = st.text_area("備註（可選）")
agree = st.checkbox("我已閱讀並同意隱私權政策與資料使用說明。")

# 寄信工具（沿用先前設計）
def _smtp_cfg():
    s = st.secrets.get("SMTP", {})
    req = ["HOST","PORT","USER","PASS","FROM","ADMIN_EMAIL"]
    miss = [k for k in req if not s.get(k)]
    if miss: return None, miss
    return s, None

def send_email(to_email: str, subject: str, body: str):
    cfg, miss = _smtp_cfg()
    if miss: return False
    msg = EmailMessage(); msg["Subject"] = subject; msg["From"] = cfg["FROM"]; msg["To"] = to_email; msg.set_content(body)
    try:
        with smtplib.SMTP(cfg["HOST"], int(cfg["PORT"])) as server:
            server.starttls(); server.login(cfg["USER"], cfg["PASS"]); server.send_message(msg)
        return True
    except Exception:
        return False

if st.button("送出預約", type="primary", disabled=not agree or not name.strip() or not phone.strip()):
    bid = BookingRepo.create({
        "case_id": case_id or None,
        "name": name.strip(),
        "phone": phone.strip(),
        "email": email.strip() or None,
        "timeslot": f"{slot}{'｜'+note.strip() if note.strip() else ''}",
    })
    EventRepo.log(case_id or "N/A", "BOOKING_CREATED", {"booking_id": bid})
    st.success("預約資訊已送出，顧問將與您聯繫！")

    cfg, miss = _smtp_cfg()
    if cfg:
        admin_body = f"新預約：#{bid} 案件:{case_id or 'N/A'} 姓名:{name} 手機:{phone} Email:{email or '—'} 時段:{slot}"
        send_email(cfg["ADMIN_EMAIL"], f"[新預約] #{bid} {name}", admin_body)
        if email:
            send_email(email, "我們已收到您的預約", f"您好 {name}，我們已收到您的預約，稍後與您聯繫。\nBooking ID: {bid}")

    # 清掉 session 中的預填避免殘留
    st.session_state.pop("incoming_case_id", None)
