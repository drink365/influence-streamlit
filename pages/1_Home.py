# pages/1_Home.py
import streamlit as st
from src.ui.footer import footer
from src.ui.theme import inject_css  # 若尚未建立，請先加入 theme.py
from pathlib import Path

st.set_page_config(page_title="傳承您的影響力｜首頁", page_icon="✨", layout="wide")
inject_css()

PRIMARY = "#BD0E1B"   # 與預約頁一致
ACCENT  = "#A88716"
INK     = "#3C3F46"
BG_SOFT = "#F7F7F8"

# 追加首頁專用 CSS
st.markdown(f"""
<style>
  .yc-hero {{
    background: linear-gradient(180deg, {BG_SOFT} 0%, #FFFFFF 100%);
    border: 1px solid rgba(0,0,0,0.04);
    border-radius: 20px;
    padding: 28px 28px;
    box-shadow: 0 8px 30px rgba(0,0,0,0.06);
  }}
  .yc-hero h1 {{ margin: .2rem 0 .5rem; font-size: 34px; color: {INK}; }}
  .yc-hero p {{ color: #555; margin: 0; font-size: 16px; }}
  .yc-badge {{
    display:inline-block; padding:6px 10px; border-radius:999px;
    background:{ACCENT}14; color:{ACCENT}; font-size:12px; font-weight:700;
    border:1px solid {ACCENT}44; letter-spacing:.3px;
  }}
  .yc-card {{
    background: #fff; border-radius: 16px; padding: 18px 18px;
    border: 1px solid rgba(0,0,0,0.06); box-shadow: 0 6px 22px rgba(0,0,0,0.05);
  }}
  .yc-cta button[kind="primary"] {{
    background:{PRIMARY} !important; border-color:{PRIMARY} !important;
    border-radius: 999px !important; font-weight: 700 !important;
  }}
  .yc-ghost button {{
    border:1px solid {PRIMARY}55 !important; color:{PRIMARY} !important; background:#fff !important;
    border-radius: 999px !important; font-weight:700 !important;
  }}
  .yc-kicker {{ color:#6b7280; font-size:13px; margin-bottom:.3rem; }}
  .yc-li li {{ line-height:1.8; }}
</style>
""", unsafe_allow_html=True)

# Logo
logo_h = Path("assets/logo-horizontal.png")
logo_v = Path("assets/logo-vertical.png")
logo_src = str(logo_h) if logo_h.exists() else (str(logo_v) if logo_v.exists() else None)

# HERO 區
with st.container():
    col_logo, col_title = st.columns([1,2], vertical_alignment="center")
    with col_logo:
        if logo_src:
            st.image(logo_src, use_column_width=True)
    with col_title:
        st.markdown('<div class="yc-hero">', unsafe_allow_html=True)
        st.markdown('<span class="yc-badge">傳承策略平台</span>', unsafe_allow_html=True)
        st.markdown("<h1>傳承您的影響力</h1>", unsafe_allow_html=True)
        st.markdown("<p>AI 智慧 × 專業顧問：60 秒快速診斷傳承風險，產出可落地的行動清單，讓資產、價值與愛同時傳承。</p>", unsafe_allow_html=True)
        st.markdown("</div>", unsafe_allow_html=True)

st.markdown("<div style='height:10px'></div>", unsafe_allow_html=True)

# 賣點 + CTA
c1, c2 = st.columns([1,1])
with c1:
    st.markdown("#### 我們能為您做什麼")
    st.markdown(
        """
        <ul class="yc-li">
          <li>個人化傳承風險儀表</li>
          <li>可視化資產地圖（股權／不動產／金融資產）</li>
          <li>建議所需流動性與保障缺口</li>
          <li>一鍵生成簡版報告（可品牌化）</li>
        </ul>
        """,
        unsafe_allow_html=True,
    )
with c2:
    st.markdown("<div class='yc-cta'>", unsafe_allow_html=True)
    go_diag = st.button("開始 60 秒診斷", type="primary", use_container_width=True)
    st.markdown("</div>", unsafe_allow_html=True)
    st.markdown("<div class='yc-ghost'>", unsafe_allow_html=True)
    go_book = st.button("預約 30 分鐘諮詢", use_container_width=True)
    st.markdown("</div>", unsafe_allow_html=True)

if go_diag:
    st.switch_page("pages/2_Diagnostic.py")
if go_book:
    st.switch_page("pages/5_Booking.py")

st.markdown("<div style='height:8px'></div>", unsafe_allow_html=True)

# 三步驟流程
st.markdown("#### 三步驟，啟動傳承行動")
x1, x2, x3 = st.columns(3)
with x1:
    st.markdown('<div class="yc-card"><b>Step 1：快速診斷</b><br>60 秒填寫，立即產出風險重點、建議流動性與保障缺口。</div>', unsafe_allow_html=True)
with x2:
    st.markdown('<div class="yc-card"><b>Step 2：方案設計</b><br>依目標與合規，整合股權／不動產／保障／信託工具。</div>', unsafe_allow_html=True)
with x3:
    st.markdown('<div class="yc-card"><b>Step 3：陪伴落地</b><br>文件、合規、資金安排、家族會議，一站式推進。</div>', unsafe_allow_html=True)

st.markdown("<div style='height:8px'></div>", unsafe_allow_html=True)

# 社會證明 區（可後續替換真實數字/Logo）
s1, s2, s3 = st.columns(3)
with s1:
    st.markdown('<div class="yc-card"><div class="yc-kicker">客戶回饋</div><b>「把複雜的傳承變簡單，每一步都可視化，我們終於有共識。」</b></div>', unsafe_allow_html=True)
with s2:
    st.markdown('<div class="yc-card"><div class="yc-kicker">顧問團隊</div>整合律師／會計師／稅務專家，跨域協作。</div>', unsafe_allow_html=True)
with s3:
    st.markdown('<div class="yc-card"><div class="yc-kicker">公開課與合作</div>長期受邀企業內訓與公開課，推廣傳承與家族治理。</div>', unsafe_allow_html=True)

st.markdown("<div style='height:10px'></div>", unsafe_allow_html=True)

# 底部 CTA
b1, b2 = st.columns([1,1])
with b1:
    if st.button("立即開始診斷", type="primary", use_container_width=True):
        st.switch_page("pages/2_Diagnostic.py")
with b2:
    if st.button("預約諮詢", use_container_width=True):
        st.switch_page("pages/5_Booking.py")

footer()
