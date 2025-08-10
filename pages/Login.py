import streamlit as st
from src.services.auth import is_whitelisted, issue_otp, verify_otp, login, logout, resolve_profile, is_logged_in, current_role

st.set_page_config(page_title="登入", page_icon="🔐", layout="centered")

st.title("🔐 顧問登入（Email OTP）")

# 顯示目前狀態
if is_logged_in():
    st.success(f"已登入：{st.session_state.get('advisor_name')}（{st.session_state.get('advisor_email')}）｜角色：{current_role()}")
    if st.button("登出"):
        logout(); st.experimental_rerun()
else:
    st.info("輸入公司白名單 Email，我們會寄送 6 位數驗證碼。若未設定 SMTP，會顯示在畫面上供測試。")

email = st.text_input("公司 Email", placeholder="name@company.com")
if st.button("寄送驗證碼"):
    if not email or "@" not in email:
        st.error("請輸入有效的 Email")
    elif not is_whitelisted(email):
        st.error("此 Email 不在白名單，請聯繫管理者新增於 .streamlit/secrets.toml 的 [ADVISORS]")
    else:
        code = issue_otp(email)
        if st.session_state.get("otp_dev_visible"):
            st.warning(f"（開發模式）未設定 SMTP，驗證碼：{code}")
        st.success("驗證碼已發送（或顯示於畫面）。請於 5 分鐘內輸入。")

otp = st.text_input("驗證碼（6 位數）", max_chars=6)
if st.button("登入"):
    if verify_otp(otp):
        name, role = resolve_profile(st.session_state.get("otp_email"))
        login(st.session_state.get("otp_email"), name, role)
        st.success(f"登入成功：{name}｜角色：{role}")
        st.experimental_rerun()
    else:
        st.error("驗證碼錯誤或已過期。請重新取得。")

st.caption("*提示：管理者可在 secrets 的 [ADVISORS] 區塊管理白名單與角色*")
