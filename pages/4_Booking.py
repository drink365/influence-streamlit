import streamlit as st
from src.repos.booking_repo import BookingRepo
from src.repos.event_repo import EventRepo

st.set_page_config(page_title="預約", page_icon="📅", layout="centered")

st.title("📅 預約顧問")
case_id = st.text_input("案件碼（可選）")
name = st.text_input("姓名/稱呼")
phone = st.text_input("手機")
email = st.text_input("Email")
slot = st.selectbox("時段", ["這週三 下午","這週五 晚上","下週一 上午","自訂（備註）"])
agree = st.checkbox("我已閱讀並同意隱私權政策與資料使用說明。")

if st.button("送出預約", disabled=not agree):
    bid = BookingRepo.create({
        "case_id": case_id or None,
        "name": name,
        "phone": phone,
        "email": email,
        "timeslot": slot,
    })
    EventRepo.log(case_id or "N/A", "BOOKING_CREATED", {"booking_id": bid})
    st.success("已送出，顧問將與您聯繫！")
