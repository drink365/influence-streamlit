# pages/2_Diagnostic.py
from datetime import datetime
from zoneinfo import ZoneInfo
import uuid
import streamlit as st
import sys
from pathlib import Path

# ---- 確保可以匯入 src/* 模組（不依賴 src.sys_path）----
ROOT = Path(__file__).resolve().parents[1]   # 專案根：含 app.py / src / pages
SRC  = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

# ---- 共用 UI（雙保險匯入）----
try:
    from src.ui.theme import inject_css
    from src.ui.footer import footer
except Exception:
    from ui.theme import inject_css
    from ui.footer import footer

# ---- 可選：寫入個案資料（存在才用）----
CasesRepo = None
Case = None
try:
    from src.repos.cases import CasesRepo, Case  # 你專案中的資料存取層
except Exception:
    try:
        from repos.cases import CasesRepo, Case
    except Exception:
        CasesRepo = None
        Case = None

st.set_page_config(page_title="家族傳承｜診斷", page_icon="🧭", layout="wide")
inject_css()
TPE = ZoneInfo("Asia/Taipei")

# ---------- 樣式 ----------
st.markdown("""
<style>
  .yc-card { background:#fff; border-radius:16px; padding:18px;
             border:1px solid rgba(0,0,0,.06); box-shadow:0 6px 22px rgba(0,0,0,.05); }
  .yc-hero { background:linear-gradient(180deg,#F7F7F8 0%,#FFF 100%);
             border-radius:20px; padding:24px 28px; }
  .yc-badge { display:inline-block; padding:6px 10px; border-radius:999px;
              background:rgba(168,135,22,0.14); color:#A88716; font-size:12px; font-weight:700;
              border:1px solid rgba(168,135,22,0.27); }
  .metric { background:#FAFAFB; border:1px dashed #E5E7EB; padding:10px 12px; border-radius:12px;}
</style>
""", unsafe_allow_html=True)

# ---------- 導頁工具（雙保險） ----------
def safe_switch(page_path: str, fallback_label: str = ""):
    try:
        st.switch_page(page_path)
    except Exception:
        if fallback_label:
            st.page_link(page_path, label=fallback_label)

# ---------- 預設狀態（避免與元件衝突，只在頁面首次建立時設） ----------
defaults = {
    "diag_equity": 0,
    "diag_realestate": 0,
    "diag_cash": 0,
    "diag_securities": 0,
    "diag_other": 0,
    "diag_insurance_cov": 0,
    "diag_focus": [],            # 多選：list[str]
    "diag_name": "",
    "diag_email": "",
    "diag_mobile": "",
}
for k, v in defaults.items():
    if k not in st.session_state:
        st.session_state[k] = v

# ---------- Hero ----------
st.markdown('<div class="yc-hero">', unsafe_allow_html=True)
st.markdown('<span class="yc-badge">快速診斷</span>', unsafe_allow_html=True)
st.subheader("輸入關鍵資訊，立即產出初步建議")
st.caption("（單位：萬元）")
st.markdown("</div>", unsafe_allow_html=True)
st.markdown("<div style='height:12px'></div>", unsafe_allow_html=True)

# ---------- 表單 ----------
st.markdown('<div class="yc-card">', unsafe_allow_html=True)
with st.form("diag_form", clear_on_submit=False):
    # 1) 資產輸入
    c1, c2, c3 = st.columns(3)
    with c1:
        st.number_input("公司股權（萬元）", min_value=0, step=10, key="diag_equity")
        st.number_input("現金／存款（萬元）", min_value=0, step=10, key="diag_cash")
    with c2:
        st.number_input("不動產（萬元）", min_value=0, step=10, key="diag_realestate")
        st.number_input("有價證券（萬元）", min_value=0, step=10, key="diag_securities")
    with c3:
        st.number_input("其他資產（萬元）", min_value=0, step=10, key="diag_other")
        st.number_input("既有保單保額（萬元）", min_value=0, step=10, key="diag_insurance_cov")

    # 即時計算（在 form 內也可以即時顯示）
    total_assets = (
        st.session_state.diag_equity
        + st.session_state.diag_realestate
        + st.session_state.diag_cash
        + st.session_state.diag_securities
        + st.session_state.diag_other
    )
    liq_need = int(round(total_assets * 0.20))  # 交棒流動性需求＝總資產×20%

    m1, m2 = st.columns(2)
    with m1:
        st.markdown(f"<div class='metric'>資產總額（萬元）：<b>{total_assets:,}</b></div>", unsafe_allow_html=True)
    with m2:
        st.markdown(f"<div class='metric'>交棒流動性需求（萬元）：<b>{liq_need:,}</b></div>", unsafe_allow_html=True)

    st.markdown("---")

    # 2) 重點關注（多選勾選）
    focus_options = [
        "交棒流動性需求", "節稅影響", "資產配置", "保障缺口",
        "股權規劃", "不動產分配", "慈善安排", "現金流穩定"
    ]
    st.write("**您的重點關注（可複選）**")
    diag_focus = st.multiselect(
        "請勾選您的重點關注（可複選）",
        options=focus_options,
        default=st.session_state.diag_focus,
        key="diag_focus",
        help="可同時勾選多個重點，以便我們在結果頁提供更貼近需求的建議。"
    )

    st.markdown("---")

    # 3) 聯絡方式
    n1, n2, n3 = st.columns(3)
    with n1:
        st.text_input("姓名（必填）", key="diag_name")
    with n2:
        st.text_input("Email（必填）", key="diag_email")
    with n3:
        st.text_input("手機（必填）", key="diag_mobile")

    # 驗證
    missing = []
    if not st.session_state.diag_name.strip():   missing.append("姓名")
    if not st.session_state.diag_email.strip():  missing.append("Email")
    if not st.session_state.diag_mobile.strip(): missing.append("手機")

    if missing:
        st.warning("尚未完成項目：" + "、".join(missing))

    submitted = st.form_submit_button("建立個案並查看結果 ➜", type="primary", disabled=bool(missing))

# ---------- 提交處理 ----------
if submitted and not missing:
    ts_local = datetime.now(TPE).strftime("%Y-%m-%d %H:%M:%S %Z")
    uid = str(uuid.uuid4())[:8].upper()
    case_id = f"CASE-{datetime.now(TPE).strftime('%Y%m%d')}-{uid}"

    # 整理資料
    focus_list = st.session_state.diag_focus or []
    focus_str = "、".join(focus_list)

    case_dict = {
        "case_id": case_id,
        "ts": ts_local,
        "name": st.session_state.diag_name.strip(),
        "email": st.session_state.diag_email.strip(),
        "mobile": st.session_state.diag_mobile.strip(),
        "equity": st.session_state.diag_equity,
        "real_estate": st.session_state.diag_realestate,
        "cash": st.session_state.diag_cash,
        "securities": st.session_state.diag_securities,
        "other_assets": st.session_state.diag_other,
        "insurance_coverage": st.session_state.diag_insurance_cov,
        "total_assets": total_assets,
        "liq_need": liq_need,             # 單一數字（總資產×20%）
        "focus": focus_str,               # 儲存為逗號樣式（實際用的是頓號）
        "focus_list": focus_list,         # 也留原始 list（給結果頁用）
    }

    # 放到 Session，供第 3 頁用
    st.session_state["current_case"] = case_dict
    st.session_state["last_case_id"] = case_id

    # 可選：寫入 CSV（若有 Repo）
    if CasesRepo and Case:
        try:
            repo = CasesRepo()
            repo.add(Case(**case_dict))
        except Exception as e:
            st.info(f"已建立個案（僅 Session），寫入資料檔時出現問題：{e}")

    # 同步傳遞預約預填給第 5 頁（日後若直接去預約）
    st.session_state["booking_prefill"] = {
        "case_id": case_id,
        "name": case_dict["name"],
        "email": case_dict["email"],
        "mobile": case_dict["mobile"],
        "need": f"重點關注：{focus_str}；交棒流動性需求約 {liq_need:,} 萬",
    }

    # 導向結果頁
    safe_switch("pages/3_Result.py", "前往結果頁")

st.markdown("</div>", unsafe_allow_html=True)

footer()
