# pages/5_Booking.py

from datetime import datetime
from zoneinfo import ZoneInfo
import smtplib, ssl
from email.message import EmailMessage
import uuid
import streamlit as st
import sys
from pathlib import Path

# --- UI 共用元件 ---
from src.ui.footer import footer
from src.ui.theme import inject_css

# ---- 強制把 src/ 加入 sys.path，然後再嘗試兩種匯入路徑 ----
ROOT = Path(__file__).resolve().parents[1]  # 專案根（含 app.py / src / pages）
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

try:
    from src.repos.bookings import BookingsRepo, Booking
except ImportError:
    from repos.bookings import BookingsRepo, Booking


# ---- 初始化 ----
inject_css()
st.markdown("## 📅 預約會議")
st.markdown("請選擇您方便的時間，我們將與您確認預約。")

# 初始化 Session State
if "user_data" not in st.session_state:
    st.session_state.user_data = {}

# 從上一頁帶入資料
default_name = st.session_state.user_data.get("name", "")
default_email = st.session_state.user_data.get("email", "")
default_phone = st.session_state.user_data.get("phone", "")

# ---- 表單 ----
with st.form("booking_form"):
    name = st.text_input("姓名", value=default_name)
    email = st.text_input("電子郵件", value=default_email)
    phone = st.text_input("電話", value=default_phone)
    date = st.date_input("預約日期")
    time = st.time_input("預約時間")
    submit = st.form_submit_button("送出預約")

# ---- 表單送出處理 ----
if submit:
    booking_datetime = datetime.combine(date, time).replace(tzinfo=ZoneInfo("Asia/Taipei"))

    # 存到資料庫
    booking_id = str(uuid.uuid4())
    booking = Booking(
        id=booking_id,
        name=name,
        email=email,
        phone=phone,
        datetime=booking_datetime,
    )
    repo = BookingsRepo()
    repo.add_booking(booking)

    # 同步更新 Session State（避免回上一頁資料消失）
    st.session_state.user_data.update({
        "name": name,
        "email": email,
        "phone": phone
    })

    # 發送確認郵件
    try:
        msg = EmailMessage()
        msg["Subject"] = "預約確認"
        msg["From"] = "your_email@example.com"
        msg["To"] = email
        msg.set_content(f"您好 {name}，\n\n您的預約已收到：{booking_datetime}\n\n謝謝！")

        context = ssl.create_default_context()
        with smtplib.SMTP_SSL("smtp.example.com", 465, context=context) as server:
            server.login("your_email@example.com", "your_password")
            server.send_message(msg)
    except Exception as e:
        st.error(f"郵件發送失敗：{e}")

    st.success(f"預約成功！我們將於 {booking_datetime} 與您確認。")

footer()
