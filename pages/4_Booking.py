import streamlit as st
from datetime import datetime
from src.repos.booking_repo import BookingRepo
from src.repos.event_repo import EventRepo

import smtplib
from email.message import EmailMessage
from email.utils import formataddr

# ======================
# 設定
# ======================
st.set_page_config(page_title="預約", page_icon="📅", layout="centered")

# 共用樣式（移植並簡化自舊版 5_Booking.py）
CSS = """
<style>
.yc-card {
  background: white;
  border-radius: 16px;
  box-shadow: 0 8px 24px rgba(0,0,0,0.07);
  padding: 24px;
  border: 1px solid rgba(0,0,0,0.06);
}
.yc-badge {
  display:inline-block;
  padding: 4px 10px;
  font-size: 12px;
  border-radius: 999px;
  background: rgba(67,97,238,.1);
  color: #4361ee;
  margin-bottom: 8px;
}
.yc-label { font-weight: 600; margin-bottom: 6px; }
.yc-hint { color: #6b7280; font-size: 12px; }
.yc-divider { border-top: 1px dashed #e5e7eb; margin: 16px 0; }
</style>
"""
st.markdown(CSS, unsafe_allow_html=True)


# ======================
# 寄信工具
# ======================
def _smtp_cfg():
    s = st.secrets.get("SMTP", {})
    required = ["HOST", "PORT", "USER", "PASS", "FROM", "ADMIN_EMAIL"]
    miss = [k for k in required if not s.get(k)]
    if miss:
        return None, miss
    return s, None

def send_email(to_email: str, subject: str, body: str):
    cfg, miss = _smtp_cfg()
    if miss:
        # 若未設定 SMTP，則略過寄信（不阻斷預約流程）
        st.info(f"通知：未設定 SMTP（缺少 {', '.join(miss)}），此環節暫不寄信。")
        return False

    msg = EmailMessage()
    msg["Subject"] = subject
    msg["From"] = cfg["FROM"]
    msg["To"] = to_email
    msg.set_content(body)

    try:
        with smtplib.SMTP(cfg["HOST"], int(cfg["PORT"])) as server:
            server.starttls()
            server.login(cfg["USER"], cfg["PASS"])
            server.send_message(msg)
        return True
    except Exception as e:
        st.warning(f"寄信失敗：{e}")
        return False


# ======================
# UI
# ======================
st.title("📅 預約顧問")
st.markdown('<div class="yc-badge">立即預約</div>', unsafe_allow_html=True)
st.caption("填寫以下資訊，顧問將儘速與您聯繫。您的資料僅用於預約與諮詢服務。")

with st.container():
    st.markdown('<div class="yc-card">', unsafe_allow_html=True)

    col1, col2 = st.columns(2)
    with col1:
        case_id = st.text_input("案件碼（可選）", placeholder="CASE-20250810-ABCD")
        name = st.text_input("姓名/稱呼*", placeholder="王先生 / Grace")
        phone = st.text_input("手機*", placeholder="09xx-xxx-xxx")
    with col2:
        email = st.text_input("Email", placeholder="name@example.com")
        slot = st.selectbox("偏好時段*", ["這週三 下午","這週五 晚上","下週一 上午","自訂（備註）"])
        note = st.text_area("備註（可選）", placeholder="若選擇自訂時段，請寫在這裡")

    st.markdown('<div class="yc-divider"></div>', unsafe_allow_html=True)
    agree = st.checkbox("我已閱讀並同意隱私權政策與資料使用說明。")
    st.caption("＊您提供的資料僅用於預約與後續聯絡。")

    disabled = not agree or (not name.strip()) or (not phone.strip())
    if st.button("送出預約", type="primary", disabled=disabled):
        # 建立預約（SQLite）
        bid = BookingRepo.create({
            "case_id": case_id or None,
            "name": name.strip(),
            "phone": phone.strip(),
            "email": email.strip() or None,
            "timeslot": f"{slot}{'｜' + note.strip() if note.strip() else ''}",
        })
        EventRepo.log(case_id or "N/A", "BOOKING_CREATED", {"booking_id": bid})

        st.success("預約資訊已送出，顧問將與您聯繫！")
        st.balloons()

        # ====== 寄信通知（若設定 SMTP） ======
        cfg, miss = _smtp_cfg()
        admin_email = cfg["ADMIN_EMAIL"] if cfg else None

        # 管理者通知信
        if admin_email:
            admin_subject = f"[新預約] #{bid} {name}"
            admin_body = (
                f"新預約已建立：\n"
                f"- Booking ID: {bid}\n"
                f"- 案件碼: {case_id or 'N/A'}\n"
                f"- 姓名/稱呼: {name}\n"
                f"- 手機: {phone}\n"
                f"- Email: {email or '未提供'}\n"
                f"- 偏好時段/備註: {slot}{'｜'+note if note else ''}\n"
                f"- 建立時間: {datetime.now():%Y-%m-%d %H:%M:%S}\n"
            )
            ok = send_email(admin_email, admin_subject, admin_body)
            if ok:
                st.toast("已通知管理者信箱 ✅", icon="✅")

        # 使用者確認信
        if email:
            user_subject = "我們已收到您的預約"
            user_body = (
                f"{name} 您好，\n\n"
                f"感謝預約！我們已收到以下資訊：\n"
                f"- Booking ID: {bid}\n"
                f"- 案件碼: {case_id or 'N/A'}\n"
                f"- 預約時段: {slot}\n"
                f"- 備註: {note or '（無）'}\n\n"
                f"顧問將盡快與您聯繫，安排後續諮詢。\n\n"
                f"— 永傳顧問團隊"
            )
            ok2 = send_email(email, user_subject, user_body)
            if ok2:
                st.toast("已寄送預約確認信 ✅", icon="📩")

    st.markdown('</div>', unsafe_allow_html=True)
