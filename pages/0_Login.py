# 登入成功後
st.session_state["user"] = username  # 儲存顧問名稱
st.success("登入成功！正在跳轉到 Dashboard...")
st.switch_page("pages/1_Dashboard.py")
