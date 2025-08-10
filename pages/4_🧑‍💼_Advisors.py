
import streamlit as st
import pandas as pd
from pathlib import Path

DATA_DIR = Path(__file__).resolve().parent.parent / "data"
ADVISORS_CSV = DATA_DIR / "advisors.csv"
ADVISORS_CSV.parent.mkdir(parents=True, exist_ok=True)

st.set_page_config(page_title="顧問專區", page_icon="🧑‍💼", layout="centered")
st.title("顧問專區")

tab1, tab2 = st.tabs(["免費註冊", "登入"])

with tab1:
    st.subheader("建立顧問帳號（免費）")
    with st.form("signup_form"):
        name = st.text_input("姓名 / 公司名")
        email = st.text_input("Email")
        phone = st.text_input("手機")
        brand = st.text_input("希望顯示於報告的顧問品牌名稱")
        if st.form_submit_button("建立帳號"):
            row = dict(name=name, email=email, phone=phone, brand=brand)
            df = pd.DataFrame([row])
            if ADVISORS_CSV.exists():
                old = pd.read_csv(ADVISORS_CSV)
                df = pd.concat([old, df], ignore_index=True)
            df.to_csv(ADVISORS_CSV, index=False)
            st.success("註冊成功！請前往『登入』使用工具。")

with tab2:
    st.subheader("登入使用工具")
    with st.form("login_form"):
        email = st.text_input("Email")
        phone = st.text_input("手機")
        if st.form_submit_button("登入"):
            ok = False
            if ADVISORS_CSV.exists():
                df = pd.read_csv(ADVISORS_CSV)
                m = df[(df["email"]==email) & (df["phone"]==phone)]
                ok = not m.empty
            if ok:
                st.session_state["advisor_email"] = email
                st.success("登入成功！請開啟『診斷』建立個案，或查看收費方案。")
                st.page_link("pages/1_🧭_Diagnostic.py", label="前往診斷（建立個案）", icon="🧭")
                st.page_link("pages/5_💳_Plans.py", label="查看方案（升級授權）", icon="💳")
            else:
                st.error("找不到帳號，請確認 Email / 手機或先註冊。")
