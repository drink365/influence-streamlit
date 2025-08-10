import streamlit as st
from src.ui.footer import footer

st.title("傳承您的影響力")
st.write("AI 智慧 + 專業顧問，打造專屬的可視化傳承方案，確保財富與愛同時流傳。")

c1, c2, c3 = st.columns(3)
with c1:
    st.markdown("### 家族資產地圖\n將股權、不動產、保單、金融資產一次整理")
with c2:
    st.markdown("### AI 傳承策略\n根據家族偏好與資料生成個人化方案")
with c3:
    st.markdown("### 行動計劃表\n明確列出下一步與時間表，陪伴落地")

st.divider()
st.subheader("立即行動")
a, b = st.columns(2)
with a:
    if st.button("開始規劃（免費）", use_container_width=True):
        st.switch_page("pages/2_Diagnostic.py")
with b:
    if st.button("預約 30 分鐘諮詢", use_container_width=True):
        st.switch_page("pages/5_Booking.py")

st.caption("免責：本平台提供之計算與建議僅供初步規劃參考，請依專業顧問複核與相關法令為準。")
footer()
