# pages/1_Home.py
import streamlit as st
from src.ui.footer import footer
from src.ui.theme import inject_css, hero, section_title, card

st.set_page_config(page_title="傳承您的影響力｜首頁", page_icon="✨", layout="wide")
inject_css()

# Hero
hero(
    title="傳承您的影響力",
    subtitle="AI 智慧 × 專業顧問：60 秒快速診斷傳承風險，產出可落地的行動清單，讓資產、價值與愛同時傳承。"
)

c1, c2 = st.columns([1,1])
with c1:
    st.markdown("<div style='height:8px'></div>", unsafe_allow_html=True)
    st.markdown("- ✅ 個人化傳承風險儀表\n- ✅ 可視化資產地圖（股權／不動產／金融資產）\n- ✅ 建議所需流動性與保障缺口\n- ✅ 一鍵生成簡版報告（可品牌化）")
with c2:
    st.markdown("<div class='yc-center yc-cta'>", unsafe_allow_html=True)
    go_diag = st.button("開始 60 秒診斷", type="primary", use_container_width=True)
    st.markdown("</div>", unsafe_allow_html=True)
    st.markdown("<div class='yc-center yc-ghost'>", unsafe_allow_html=True)
    go_book = st.button("預約 30 分鐘諮詢", use_container_width=True)
    st.markdown("</div>", unsafe_allow_html=True)

if go_diag:
    st.switch_page("pages/2_Diagnostic.py")
if go_book:
    st.switch_page("pages/5_Booking.py")

# 三大賣點
section_title("我們的優勢", "為高資產家族而生的傳承規劃")
a, b, c = st.columns(3)
with a: card("一體化視角", "資產類型 × 家族結構 × 法規變動，形成可操作的「全貌」，避免規劃盲點。")
with b: card("AI + 專業雙引擎", "用 AI 快速完成盤點、試算與文件初稿，再由顧問校準、落地。")
with c: card("行動清單導向", "清楚下一步、時間表與責任人，讓傳承不再停留在討論。")

# 三步驟流程
section_title("服務流程", "三步驟，啟動傳承行動")
x1, x2, x3 = st.columns(3)
with x1: card("Step 1：快速診斷", "60 秒填寫，立即產出風險重點、建議流動性與保障缺口。")
with x2: card("Step 2：方案設計", "由顧問依目標與法規，整合股權／不動產／保單／信託工具。")
with x3: card("Step 3：陪伴落地", "文件、節稅合規、資金安排、家族會議，一站式推進。")

# 社會證明（占位）
section_title("信任我們", "過去的合作與肯定")
s1, s2, s3 = st.columns(3)
with s1: card("客戶回饋（摘）", "「把複雜的傳承計畫變簡單，每一步都可視化，我們家族終於有共識。」")
with s2: card("顧問團隊", "整合律師／會計師／稅務專家，提供跨領域解決方案。")
with s3: card("公開課與合作", "長期受邀企業內訓與公開課，推廣傳承與家族治理。")

# 底部 CTA
st.markdown("<div style='height:8px'></div>", unsafe_allow_html=True)
ccta1, ccta2 = st.columns([1,1])
with ccta1:
    if st.button("立即開始診斷", type="primary", use_container_width=True):
        st.switch_page("pages/2_Diagnostic.py")
with ccta2:
    if st.button("預約諮詢", use_container_width=True):
        st.switch_page("pages/5_Booking.py")

# 頁尾
footer()
