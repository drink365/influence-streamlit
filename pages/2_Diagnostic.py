# pages/2_Diagnostic.py
import uuid
from datetime import datetime
from zoneinfo import ZoneInfo
from pathlib import Path

import streamlit as st

from src.ui.footer import footer
from src.ui.theme import inject_css
from src.repos.cases import CaseRepo
from src.config import DATA_DIR

# ---------------- 基本設定 / 風格 ----------------
st.set_page_config(page_title="60 秒傳承風險診斷", page_icon="🧭", layout="wide")
inject_css()

PRIMARY = "#BD0E1B"
ACCENT  = "#A88716"
INK     = "#3C3F46"
BG_SOFT = "#F7F7F8"
TPE = ZoneInfo("Asia/Taipei")

st.markdown(f"""
<style>
  .yc-hero {{
    background: linear-gradient(180deg, {BG_SOFT} 0%, #FFFFFF 100%);
    border: 1px solid rgba(0,0,0,0.04);
    border-radius: 20px;
    padding: 24px 28px;
    box-shadow: 0 8px 30px rgba(0,0,0,0.06);
  }}
  .yc-hero h1 {{ margin: .2rem 0 .5rem; font-size: 28px; color: {INK}; }}
  .yc-hero p {{ color: #555; margin: 0; }}
  .yc-badge {{
    display:inline-block; padding:6px 10px; border-radius:999px;
    background:{ACCENT}14; color:{ACCENT}; font-size:12px; font-weight:700;
    border:1px solid {ACCENT}44; letter-spacing:.3px;
  }}
  .yc-card {{
    background: #fff; border-radius: 16px; padding: 18px 18px;
    border: 1px solid rgba(0,0,0,0.06); box-shadow: 0 6px 22px rgba(0,0,0,0.05);
  }}
  .yc-step {{ display:flex; gap:.6rem; align-items:center; margin:.4rem 0 1rem; color:#374151; font-weight:700; }}
  .yc-dot  {{ width:26px; height:26px; border-radius:999px; background:{PRIMARY}11; border:1px solid {PRIMARY}55; display:flex; align-items:center; justify-content:center; font-size:12px; color:{PRIMARY}; }}
  .yc-cta button[kind="primary"] {{ background:{PRIMARY} !important; border-color:{PRIMARY} !important; border-radius:999px !important; font-weight:700 !important; }}
  .yc-muted {{ color:#666; font-size:13px; }}
</style>
""", unsafe_allow_html=True)

# --------- 若上一輪已要求跳轉，先處理（避免在 form 回調中 switch 失效） ---------
if st.session_state.get("__go_result__", False):
    st.session_state["__go_result__"] = False
    st.switch_page("pages/3_Result.py")

# ---------------- 檔案/Repo 安全 ----------------
try:
    Path(DATA_DIR).mkdir(parents=True, exist_ok=True)
except Exception as e:
    st.error(f"無法建立資料夾 data/：{e}")

repo = CaseRepo()  # 診斷頁只做 add()

# ---------------- Hero 區 ----------------
st.markdown('<div class="yc-hero">', unsafe_allow_html=True)
st.markdown('<span class="yc-badge">快速診斷</span>', unsafe_allow_html=True)
st.markdown("<h1>60 秒傳承風險診斷</h1>", unsafe_allow_html=True)
st.markdown("<p>填完即可看到您的風險重點、建議流動性與保障缺口。完成後可產出簡版報告。</p>", unsafe_allow_html=True)
st.markdown("</div>", unsafe_allow_html=True)

st.markdown("<div style='height:12px'></div>", unsafe_allow_html=True)

# ---------------- 表單狀態 ----------------
if "diag_last_case" not in st.session_state:
    st.session_state.diag_last_case = None

# ---------------- 表單開始（只用 form_submit_button；不混用 st.button） ----------------
with st.form("diag_form", clear_on_submit=False):
    # Step 1：基本資料
    st.markdown('<div class="yc-step"><div class="yc-dot">1</div><div>基本資料</div></div>', unsafe_allow_html=True)
    base_c1, base_c2, base_c3 = st.columns([1,1,1])
    with base_c1:
        name = st.text_input("姓名 *", placeholder="王大明")
    with base_c2:
        email = st.text_input("Email *", placeholder="name@example.com")
    with base_c3:
        mobile = st.text_input("手機 *", placeholder="+886 9xx xxx xxx")

    fam_c1, fam_c2, fam_c3 = st.columns([1,1,1])
    with fam_c1:
        marital = st.selectbox("婚姻狀況 *", ["未婚","已婚","離婚","喪偶"])
    with fam_c2:
        children = st.number_input("子女人數 *", min_value=0, max_value=10, step=1, value=0)
    with fam_c3:
        heirs_ready = st.selectbox("是否已有接班人選 *", ["尚未明確","已明確"])

    st.markdown("<hr style='margin:10px 0 16px; opacity:.15'>", unsafe_allow_html=True)

    # Step 2：資產盤點（金額單位：萬元）
    st.markdown('<div class="yc-step"><div class="yc-dot">2</div><div>資產盤點（萬元）</div></div>', unsafe_allow_html=True)
    a1, a2, a3, a4 = st.columns(4)
    with a1:
        equity = st.number_input("公司股權 *", min_value=0, step=10, value=0)
    with a2:
        real_estate = st.number_input("不動產 *", min_value=0, step=10, value=0)
    with a3:
        financial = st.number_input("金融資產 *", min_value=0, step=10, value=0, help="現金/存款/基金/股票等")
    with a4:
        insurance_cov = st.number_input("既有保單保額 *", min_value=0, step=10, value=0)

    total_assets = equity + real_estate + financial + insurance_cov
    st.caption(f"目前估算總資產：約 **{total_assets:,} 萬**（僅供初步參考）")

    st.markdown("<hr style='margin:10px 0 16px; opacity:.15'>", unsafe_allow_html=True)

    # Step 3：重點關注
    st.markdown('<div class="yc-step"><div class="yc-dot">3</div><div>重點關注</div></div>', unsafe_allow_html=True)
    focus = st.multiselect(
        "請選擇最多 3 項您最在意的議題",
        options=["節稅安排","現金流穩定","股權交棒","家族治理","風險隔離","資產隔代傳承","慈善安排","文件與合規"],
        default=["節稅安排","股權交棒"],
        max_selections=3,
    )
    target_years = st.slider("希望在幾年內完成主要傳承安排？", 1, 10, 3)

    # Step 4：送出
    st.markdown("<hr style='margin:10px 0 16px; opacity:.15'>", unsafe_allow_html=True)
    st.markdown('<div class="yc-step"><div class="yc-dot">4</div><div>送出診斷</div></div>', unsafe_allow_html=True)
    agree = st.checkbox("我了解此為初步診斷，結果僅供參考；若需實務落地將由專業顧問協助。", value=True)

    st.markdown("<div class='yc-cta'>", unsafe_allow_html=True)
    submitted = st.form_submit_button("查看診斷結果 ➜", type="primary", use_container_width=True)
    st.markdown("</div>", unsafe_allow_html=True)

# ---------------- 提交後處理 ----------------
if submitted:
    missing = []
    if not name.strip(): missing.append("姓名")
    if not email.strip(): missing.append("Email")
    if not mobile.strip(): missing.append("手機")
    if total_assets <= 0: missing.append("資產盤點")
    if not agree: missing.append("同意聲明")

    if missing:
        st.error("請完成必填項目： " + "、".join(missing))
    else:
        case_id = f"CASE-{datetime.now(TPE).strftime('%Y%m%d')}-{str(uuid.uuid4())[:8].upper()}"
        ts_local = datetime.now(TPE).strftime("%Y-%m-%d %H:%M:%S %Z")

        payload = {
            "ts": ts_local,
            "case_id": case_id,
            "name": name.strip(),
            "email": email.strip(),
            "mobile": mobile.strip(),
            "marital": marital,
            "children": children,
            "heirs_ready": heirs_ready,
            "equity": equity,
            "real_estate": real_estate,
            "financial": financial,
            "insurance_cov": insurance_cov,
            "total_assets": total_assets,
            "focus": "、".join(focus),
            "target_years": target_years,
            "status": "created",
        }

        try:
            repo.add(payload)                  # 寫入 cases.csv
            st.toast("✅ 已建立個案", icon="✅")
            st.session_state["diag_last_case"] = case_id
            st.session_state["last_case_id"] = case_id  # 給結果頁用
            st.session_state["__go_result__"] = True    # 導頁旗標
            st.rerun()
        except Exception as e:
            st.error(f"寫入個案資料時發生錯誤：{e}")

# ---------------- 頁尾 ----------------
footer()
