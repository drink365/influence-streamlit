
import streamlit as st

st.set_page_config(page_title="預約諮詢", page_icon="📅", layout="centered")
st.title("預約 30 分鐘線上會談")

st.write("請選擇您方便的時間，或留下聯絡資訊，我們將盡快與您聯繫。")
st.info("（若您使用 Calendly / Google 日曆連結，可直接在此嵌入 iframe）")

with st.form("book_form"):
    name = st.text_input("姓名")
    phone = st.text_input("手機")
    email = st.text_input("Email")
    notes = st.text_area("想先告訴我們的情況（選填）")
    if st.form_submit_button("送出預約申請"):
        st.success("已收到預約申請，我們將盡快與您聯繫。")
