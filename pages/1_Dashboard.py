import streamlit as st
from datetime import datetime

# 頁面設定
st.set_page_config(page_title="顧問工作台", layout="wide")

# 取得登入顧問名稱（假設存在 session state）
advisor_name = st.session_state.get("advisor_name", "顧問")

# 歡迎詞
st.title(f"👋 歡迎回來，{advisor_name}！")
st.caption(f"今天是 {datetime.now().strftime('%Y-%m-%d')}，祝您規劃順利。")

st.markdown("---")

# 三大指標數據（可以連資料庫動態取得）
col1, col2, col3 = st.columns(3)

with col1:
    st.metric("今日登入人數", 15, delta="+3")
with col2:
    st.metric("本月新增客戶", 8, delta="+2")
with col3:
    st.metric("本月完成規劃案", 3, delta="-1")

st.markdown("---")

# 快速連結功能
st.subheader("📌 快速進入工具")
col_a, col_b, col_c = st.columns(3)

with col_a:
    if st.button("🩺 開始診斷", use_container_width=True):
        st.switch_page("pages/2_Diagnostic.py")

with col_b:
    if st.button("📄 規劃報告", use_container_width=True):
        st.switch_page("pages/3_Result.py")

with col_c:
    if st.button("📅 活動管理", use_container_width=True):
        st.switch_page("pages/7_Events_Admin.py")

st.markdown("---")

# 後續可以加最新活動、最近修改紀錄等
st.subheader("📰 最新消息")
st.info("目前系統測試版本，部分功能尚在開發中。")
