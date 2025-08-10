
import streamlit as st

st.set_page_config(page_title="授權與方案", page_icon="💳", layout="wide")
st.title("授權與高階會員方案（合規）")

col1, col2 = st.columns(2)

with col1:
    st.header("Starter（授權）")
    st.write("- AI 診斷、提案草案、案例庫（基礎）  
"
             "- 下載帶您品牌的簡版報告（白標）  
"
             "- 客戶個案資料保存與版本歷程  
"
             "- **NT$ 3,600 / 月** 或 **NT$ 36,000 / 年**")
with col2:
    st.header("Pro（高階會員）")
    st.write("- 進階策略模組與圖像化報告客製  
"
             "- 專屬培訓與話術庫、實戰案例包  
"
             "- 專案協作席次 3 位（團隊版）  
"
             "- **NT$ 12,000 / 月** 或 **NT$ 120,000 / 年**")

st.divider()
st.caption("合規說明：平台僅收授權與專業服務費，不參與佣金分配或分潤。")
