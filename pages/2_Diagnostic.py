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
TPE = ZoneInfo("Asia/Taipei")

# ---- 單次導頁旗標（成功送出後才會設定；這裡用完即清）----
go_case = st.session_state.pop("__go_result_case", None)
if isinstance(go_case, str) and go_case:
    st.session_state["last_case_id"] = go_case
    st.switch_page("pages/3_Result.py")

# ---- 預設值（僅首次設定；之後都用 session_state 持有最新值）----
defaults = {
    "diag_name": "", "diag_email": "", "diag_mobile": "",
    "diag_marital": "未婚", "diag_children": 0, "diag_heirs": "尚未明確",
    "diag_equity": 0, "diag_re": 0, "diag_fin": 0, "diag_cov": 0,
    "diag_focus": ["節稅安排", "股權交棒"], "diag_years": 3, "diag_agree": True,
}
for k, v in defaults.items():
    st.session_state.setdefault(k, v)

# ---- 檔案 / Repo ----
Path(DATA_DIR).mkdir(parents=True, exist_ok=True)
repo = CaseRepo()

# ---- 樣式 ----
st.markdown("""
<style>
  .yc-hero { background:linear-gradient(180deg,#F7F7F8 0%,#FFF 100%);
             border:1px solid #0001; border-radius:20px; padding:24px 28px;
             box-shadow:0 8px 30px #0001; }
  .yc-badge { display:inline-block; padding:6px 10px; border-radius:999px;
              background:rgba(168,135,22,.12); color:#A88716; font-size:12px; font-weight:700;
              border:1px solid rgba(168,135,22,.28); }
  .yc-step { display:flex; gap:.6rem; align-items:center; margin:.4rem 0 1rem; color:#374151; font-weight:700; }
  .yc-dot  { width:26px; height:26px; border-radius:999px; background:rgba(189,14,27,.08); border:1px solid rgba(189,14,27,.35);
             display:flex; align-items:center; justify-content:center; font-size:12px; color:#BD0E1B; }
  .yc-cta  button[kind="primary"] { background:#BD0E1B !important; border-color:#BD0E1B !important;
              border-radius:999px !important; font-weight:700 !important; }
  .yc-alert { background:#fff9f0; border:1px solid #facc15; color:#92400e; padding:8px 12px; border-radius:10px; font-size:13px; }
</style>
""", unsafe_allow_html=True)

# ---- Hero ----
st.markdown('<div class="yc-hero">', unsafe_allow_html=True)
st.markdown('<span class="yc-badge">快速診斷</span>', unsafe_allow_html=True)
st.markdown("<h1>60 秒傳承風險診斷</h1>", unsafe_allow_html=True)
st.markdown("<p>填完即可看到您的風險重點、建議流動性與保障缺口。</p>", unsafe_allow_html=True)
st.markdown("</div>", unsafe_allow_html=True)
st.markdown("<div style='height:12px'></div>", unsafe_allow_html=True)

# ---- 快速動作：清除本次填寫（同時清掉導航旗標）----
c_reset, _ = st.columns([1, 7])
with c_reset:
    if st.button("🧹 清除本次填寫", use_container_width=True):
        for k, v in defaults.items():
            st.session_state[k] = v
        st.session_state.pop("__go_result_case", None)
        st.session_state.pop("last_case_id", None)
        st.rerun()

# ---------------- 基本資料（非 form，輸入即時 rerun） ----------------
st.markdown('<div class="yc-step"><div class="yc-dot">1</div><div>基本資料</div></div>', unsafe_allow_html=True)
bc1, bc2, bc3 = st.columns(3)
with bc1: st.text_input("姓名 *",  key="diag_name")
with bc2: st.text_input("Email *", key="diag_email")
with bc3: st.text_input("手機 *",  key="diag_mobile")

fc1, fc2, fc3 = st.columns(3)
with fc1: st.selectbox("婚姻狀況 *", ["未婚","已婚","離婚","喪偶"], key="diag_marital")
with fc2: st.number_input("子女人數 *", 0, 10, key="diag_children")
with fc3: st.selectbox("是否已有接班人選 *", ["尚未明確","已明確"], key="diag_heirs")

st.markdown("<hr style='margin:10px 0 16px; opacity:.15'>", unsafe_allow_html=True)

# ---------------- 資產盤點（即時總額） ----------------
st.markdown('<div class="yc-step"><div class="yc-dot">2</div><div>資產盤點（萬元）</div></div>', unsafe_allow_html=True)
a1, a2, a3, a4 = st.columns(4)
with a1: st.number_input("公司股權 *",    min_value=0, step=10, key="diag_equity")
with a2: st.number_input("不動產 *",      min_value=0, step=10, key="diag_re")
with a3: st.number_input("金融資產 *",    min_value=0, step=10, key="diag_fin", help="現金/存款/基金/股票等")
with a4: st.number_input("既有保單保額 *", min_value=0, step=10, key="diag_cov")

total_assets = st.session_state["diag_equity"] + st.session_state["diag_re"] + st.session_state["diag_fin"] + st.session_state["diag_cov"]
st.caption(f"目前估算總資產：約 **{total_assets:,} 萬**（僅供初步參考）")

st.markdown("<hr style='margin:10px 0 16px; opacity:.15'>", unsafe_allow_html=True)

# ---------------- 重點關注 ----------------
st.markdown('<div class="yc-step"><div class="yc-dot">3</div><div>重點關注</div></div>', unsafe_allow_html=True)
st.multiselect(
    "請選擇最多 3 項您最在意的議題",
    options=["節稅安排","現金流穩定","股權交棒","家族治理","風險隔離","資產隔代傳承","慈善安排","文件與合規"],
    key="diag_focus",           # 只用 key 控制；不要再給 default=
    max_selections=3,
)
st.slider("希望在幾年內完成主要傳承安排？", 1, 10, key="diag_years")

st.markdown("<hr style='margin:10px 0 16px; opacity:.15'>", unsafe_allow_html=True)

# ---------------- 送出（按鈕鎖定；Enter 不會誤送出） ----------------
st.checkbox("我了解此為初步診斷，結果僅供參考；若需實務落地將由專業顧問協助。", key="diag_agree")

missing = []
if not st.session_state["diag_name"].strip():   missing.append("姓名")
if not st.session_state["diag_email"].strip():  missing.append("Email")
if not st.session_state["diag_mobile"].strip(): missing.append("手機")
if total_assets <= 0:                            missing.append("資產盤點")
if not st.session_state["diag_agree"]:          missing.append("同意聲明")

if missing:
    st.markdown("<div class='yc-alert'>尚未完成項目：" + "、".join(missing) + "</div>", unsafe_allow_html=True)

submit = st.button("查看診斷結果 ➜", type="primary", use_container_width=True, disabled=bool(missing))

# ---------------- 送出後處理（成功才導頁） ----------------
if submit and not missing:
    case_id = f"CASE-{datetime.now(TPE).strftime('%Y%m%d')}-{str(uuid.uuid4())[:8].upper()}"
    ts_local = datetime.now(TPE).strftime("%Y-%m-%d %H:%M:%S %Z")
    payload = {
        "ts": ts_local, "case_id": case_id,
        "name": st.session_state["diag_name"].strip(),
        "email": st.session_state["diag_email"].strip(),
        "mobile": st.session_state["diag_mobile"].strip(),
        "marital": st.session_state["diag_marital"],
        "children": st.session_state["diag_children"],
        "heirs_ready": st.session_state["diag_heirs"],
        "equity": st.session_state["diag_equity"],
        "real_estate": st.session_state["diag_re"],
        "financial": st.session_state["diag_fin"],
        "insurance_cov": st.session_state["diag_cov"],
        "total_assets": total_assets,
        "focus": "、".join(st.session_state["diag_focus"]),
        "target_years": st.session_state["diag_years"],
        "status": "created",
    }
    try:
        repo.add(payload)
        st.toast("✅ 已建立個案", icon="✅")
        st.session_state["__go_result_case"] = case_id  # 單次旗標（只在成功後設置）
        st.rerun()
    except Exception as e:
        st.error(f"寫入個案資料時發生錯誤：{e}")

footer()
