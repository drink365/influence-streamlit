
import streamlit as st

st.set_page_config(page_title="影響力｜永傳家族傳承平台", page_icon="✨", layout="wide")

st.markdown("# 傳承您的影響力")
st.write("讓家族的資產、價值觀與故事，安心交棒到下一代。")
st.write("AI 智慧 + 專業顧問，打造專屬的可視化傳承方案，確保財富與愛同時流傳。")

col1, col2 = st.columns(2)
with col1:
    st.page_link("pages/1_Diagnostic.py", label="開始規劃（免費）")
with col2:
    st.page_link("pages/4_Advisors.py", label="顧問專區")

st.divider()
st.subheader("為什麼是現在？")
st.markdown("- 正在迎來史上規模最大的財富交棒潮  
"
            "- 高資產家族的三大挑戰：資產分配協調、跨境合規、下一代準備  
"
            "- 我們的解法：**全景可視化 → 策略具體化 → 行動標準化**")

st.divider()
st.subheader("我們能為您做什麼")
c1, c2, c3 = st.columns(3)
with c1:
    st.markdown("**家族資產地圖**  
將股權、不動產、保單、金融資產一次整理")
with c2:
    st.markdown("**AI 傳承策略**  
根據家族偏好與資料生成個人化方案")
with c3:
    st.markdown("**行動計劃表**  
明確列出下一步與時間表，陪伴落地")

st.divider()
st.subheader("立即行動")
colA, colB = st.columns(2)
with colA:
    st.page_link("pages/1_Diagnostic.py", label="立即免費體驗")
with colB:
    st.page_link("pages/3_Book.py", label="預約 30 分鐘諮詢")

st.divider()
st.caption("免責：本平台提供之計算與建議僅供初步規劃參考，請依專業顧問複核與相關法令為準。")
