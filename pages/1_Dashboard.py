import streamlit as st

st.set_page_config(page_title="顧問 Dashboard", page_icon="📊", layout="wide")

# 檢查是否登入
if "user" not in st.session_state:
    st.warning("請先登入")
    st.stop()

st.title(f"📊 顧問 Dashboard - 歡迎 {st.session_state['user']}")

# 模擬顧問資料
clients = [
    {"姓名": "王小明", "狀態": "問卷完成", "提案進度": "50%"},
    {"姓名": "李小華", "狀態": "等待填寫問卷", "提案進度": "0%"},
    {"姓名": "張美麗", "狀態": "提案已送出", "提案進度": "100%"},
]

st.subheader("📋 客戶清單")
st.table(clients)

st.subheader("🚀 快速操作")
col1, col2, col3 = st.columns(3)
with col1:
    if st.button("➕ 新增客戶"):
        st.switch_page("pages/2_Client_Form.py")  # 之後建立的客戶問卷頁
with col2:
    st.button("📄 建立提案")
with col3:
    st.button("📊 查看分析報告")
