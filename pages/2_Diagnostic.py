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

st.set_page_config(page_title="60 秒傳承風險診斷", page_icon="🧭", layout="wide")
inject_css()

PRIMARY = "#BD0E1B"; ACCENT = "#A88716"; INK = "#3C3F46"; BG_SOFT = "#F7F7F8"
TPE = ZoneInfo("Asia/Taipei")

st.markdown(f"""
<style>
  .yc-hero {{background:linear-gradient(180deg,{BG_SOFT} 0%,#FFF 100%);border:1px solid #0001;border-radius:20px;padding:24px 28px;box-shadow:0 8px 30px #0001}}
  .yc-badge {{display:inline-block;padding:6px 10px;border-radius:999px;background:{ACCENT}14;color:{ACCENT};font-size:12px;font-weight:700;border:1px solid {ACCENT}44}}
  .yc-card {{background:#fff;border-radius:16px;padding:18px;border:1px solid #0001;box-shadow:0 6px 22px #0001}}
  .yc-step {{display:flex;gap:.6rem;align-items:center;margin:.4rem 0 1rem;color:#374151;font-weight:700}}
  .yc-dot {{width:26px;height:26px;border-radius:999px;background:{PRIMARY}11;border:1px solid {PRIMARY}55;display:flex;align-items:center;justify-content:center;font-size:12px;color:{PRIMARY}} 
  .yc-cta button[kind="primary"]{{background:{PRIMARY}!important;border-color:{PRIMARY}!important;border-radius:999px!important;font-weight:700!important}}
  .yc-alert {{background:#fff9f0;border:1px solid #facc15;color:#92400e;padding:8px 12px;border-radius:10px;font-size:13px}}
</style>""", unsafe_allow_html=True)

# --- 單次導頁旗標（成功送出後才會設定；這裡用完即清） ---
go_case = st.session_state.pop("__go_result_case", None)
if go_case:
    st.session_state["last_case_id"] = go_case
    st.switch_page("pages/3_Result.py")

# --- 檔案 / repo ---
Path(DATA_DIR).mkdir(parents=True, exist_ok=True)
repo = CaseRepo()

# --- Hero ---
st.markdown('<div class="yc-hero">', unsafe_allow_html=True)
st.markdown('<span class="yc-badge">快速診斷</span>', unsafe_allow_html=True)
st.markdown("<h1>60 秒傳承風險診斷</h1>", unsafe_allow_html=True)
st.markdown("<p>填完即可看到您的風險重點、建議流動性與保障缺口。</p>", unsafe_allow_html=True)
st.markdown("</div>", unsafe_allow_html=True)
st.markdown("<div style='height:12px'></div>", unsafe_allow_html=True)

# ---------------- 基本資料（不使用 form，讓輸入即時 rerun） ----------------
st.markdown('<div class="yc-step"><div class="yc-dot">1</div><div>基本資料</div></div>', unsafe_allow_html=True)
bc1, bc2, bc3 = st.columns(3)
with bc1: name   = st.text_input("姓名 *", key="diag_name")
with bc2: email  = st.text_input("Email *", key="diag_email")
with bc3: mobile = st.text_input("手機 *", key="diag_mobile")

fc1, fc2, fc3 = st.columns(3)
with fc1: marital     = st.selectbox("婚姻狀況 *", ["未婚","已婚","離婚","喪偶"], key="diag_marital")
with fc2: children    = st.number_input("子女人數 *", 0, 10, 0, 1, key="diag_children")
with fc3: heirs_ready = st.selectbox("是否已有接班人選 *", ["尚未明確","已明確"], key="diag_heirs")

st.markdown("<hr style='margin:10px 0 16px; opacity:.15'>", unsafe_allow_html=True)

# ---------------- 資產盤點（即時總額） ----------------
st.markdown('<div class="yc-step"><div class="yc-dot">2</div><div>資產盤點（萬元）</div></div>', unsafe_allow_html=True)
a1, a2, a3, a4 = st.columns(4)
with a1: equity        = st.number_input("公司股權 *", min_value=0, step=10, value=st.session_state.get("diag_equity", 0), key="diag_equity")
with a2: real_estate   = st.number_input("不動產 *",   min_value=0, step=10, value=st.session_state.get("diag_re", 0),       key="diag_re")
with a3: financial     = st.number_input("金融資產 *", min_value=0, step=10, value=st.session_state.get("diag_fin", 0),      key="diag_fin", help="現金/存款/基金/股票等")
with a4: insurance_cov = st.number_input("既有保單保額 *", min_value=0, step=10, value=st.session_state.get("diag_cov", 0), key="diag_cov")

total_assets = (st.session_state.get("diag_equity",0) +
                st.session_state.get("diag_re",0) +
                st.session_state.get("diag_fin",0) +
                st.session_state.get("diag_cov",0))
st.caption(f"目前估算總資產：約 **{total_assets:,} 萬**（僅供初步參考）")

st.markdown("<hr style='margin:10px 0 16px; opacity:.15'>", unsafe_allow_html=True)

# ---------------- 重點關注 ----------------
st.markdown('<div class="yc-step"><div class="yc-dot">3</div><div>重點關注</div></div>', unsafe_allow_html=True)
focus = st.multiselect(
    "請選擇最多 3 項您最在意的議題",
    options=["節稅安排","現金流穩定","股權交棒","家族治理","風險隔離","資產隔代傳承","慈善安排","文件與合規"],
    default=st.session_state.get("diag_focus", ["節稅安排","股權交棒"]),
    max_selections=3,
    key="diag_focus"
)
target_years = st.slider("希望在幾年內完成主要傳承安排？", 1, 10, st.session_state.get("diag_years",3), key="diag_years")

st.markdown("<hr style='margin:10px 0 16px; opacity:.15'>", unsafe_allow_html=True)

# ---------------- 送出（按鈕鎖定，未完成不可送出） ----------------
agree = st.checkbox("我了解此為初步診斷，結果僅供參考；若需實務落地將由專業顧問協助。", value=st.session_state.get("diag_agree", True), key="diag_agree")

missing_live = []
if not (name or "").strip():     missing_live.append("姓名")
if not (email or "").strip():    missing_live.append("Email")
if not (mobile or "").strip():   missing_live.append("手機")
if total_assets <= 0:            missing_live.append("資產盤點")
if not agree:                    missing_live.append("同意聲明")

if missing_live:
    st.markdown("<div class='yc-alert'>尚未完成項目："
                + "、".join(missing_live) + "</div>", unsafe_allow_html=True)

is_ready = (len(missing_live) == 0)

submit = st.button("查看診斷結果 ➜", type="primary", use_container_width=True, disabled=not is_ready)

# ---------------- 送出後處理（成功才導頁） ----------------
if submit and is_ready:
    case_id = f"CASE-{datetime.now(TPE).strftime('%Y%m%d')}-{str(uuid.uuid4())[:8].upper()}"
    ts_local = datetime.now(TPE).strftime("%Y-%m-%d %H:%M:%S %Z")
    payload = {
        "ts": ts_local, "case_id": case_id,
        "name": name.strip(), "email": email.strip(), "mobile": mobile.strip(),
        "marital": marital, "children": children, "heirs_ready": heirs_ready,
        "equity": st.session_state["diag_equity"],
        "real_estate": st.session_state["diag_re"],
        "financial": st.session_state["diag_fin"],
        "insurance_cov": st.session_state["diag_cov"],
        "total_assets": total_assets,
        "focus": "、".join(st.session_state.get("diag_focus", [])),
        "target_years": st.session_state.get("diag_years", 3),
        "status": "created",
    }
    try:
        CaseRepo().add(payload)
        st.toast("✅ 已建立個案", icon="✅")
        st.session_state["__go_result_case"] = case_id   # 單次旗標
        st.rerun()
    except Exception as e:
        st.error(f"寫入個案資料時發生錯誤：{e}")

footer()
