# pages/3_Result.py
from datetime import datetime
from zoneinfo import ZoneInfo
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

# ---- 可選：讀取個案（存在才用；若 session 沒資料時用 last_case_id 補）----
CasesRepo = None
try:
    from src.repos.cases import CasesRepo
except Exception:
    try:
        from repos.cases import CasesRepo
    except Exception:
        CasesRepo = None

st.set_page_config(page_title="家族傳承｜診斷結果", page_icon="📊", layout="wide")
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
  .metric { background:#FAFAFB; border:1px dashed #E5E7EB; padding:14px 16px; border-radius:12px;}
  .list { margin: 0 0 0 1rem; padding:0; }
  .list li { margin: 4px 0; }
</style>
""", unsafe_allow_html=True)

# ---------- 導頁工具（雙保險） ----------
def safe_switch(page_path: str, fallback_label: str = ""):
    try:
        st.switch_page(page_path)
    except Exception:
        if fallback_label:
            st.page_link(page_path, label=fallback_label)

# ---------- 取得個案資料 ----------
case = st.session_state.get("current_case")

# 若 session 沒有，嘗試用 last_case_id 從資料層補回
if not case and CasesRepo and st.session_state.get("last_case_id"):
    try:
        repo = CasesRepo()
        case = repo.get_by_case_id(st.session_state["last_case_id"])  # 你的 repos 需有這方法
    except Exception:
        case = None

if not case:
    st.warning("尚未找到個案資料，請先完成診斷。")
    if st.button("返回診斷"):
        safe_switch("pages/2_Diagnostic.py", "返回診斷")
    footer()
    st.stop()

# 保底欄位
name = case.get("name", "")
email = case.get("email", "")
mobile = case.get("mobile", "")
case_id = case.get("case_id", "")
total_assets = int(case.get("total_assets", 0) or 0)
liq_need = int(case.get("liq_need", round(total_assets * 0.2)) or 0)
focus_list = case.get("focus_list") or []
focus_str = case.get("focus") or "、".join(focus_list)

# ---------- Hero ----------
st.markdown('<div class="yc-hero">', unsafe_allow_html=True)
st.markdown('<span class="yc-badge">診斷結果</span>', unsafe_allow_html=True)
st.subheader("您的初步傳承規劃建議")
if case_id:
    st.caption(f"個案編號：{case_id}")
st.markdown("</div>", unsafe_allow_html=True)
st.markdown("<div style='height:12px'></div>", unsafe_allow_html=True)

# ---------- 關鍵數字 ----------
st.markdown('<div class="yc-card">', unsafe_allow_html=True)
m1, m2, m3 = st.columns([1,1,1])
with m1:
    st.markdown(f"<div class='metric'>資產總額（萬元）<br><b style='font-size:22px'>{total_assets:,}</b></div>", unsafe_allow_html=True)
with m2:
    st.markdown(f"<div class='metric'>交棒流動性需求（萬元）<br><b style='font-size:22px'>{liq_need:,}</b></div>", unsafe_allow_html=True)
with m3:
    st.markdown(f"<div class='metric'>既有保單保額（萬元）<br><b style='font-size:22px'>{int(case.get('insurance_coverage',0) or 0):,}</b></div>", unsafe_allow_html=True)

st.markdown("---")

# ---------- 重點關注（條列顯示） ----------
st.markdown("**您的重點關注**")
if focus_list:
    st.markdown("<ul class='list'>" + "".join([f"<li>{item}</li>" for item in focus_list]) + "</ul>", unsafe_allow_html=True)
else:
    st.caption("（尚未勾選）")

st.markdown("---")

# ---------- 初步建議（依重點關注動態產出簡述） ----------
st.markdown("**初步建議摘要**")
suggestions = []
if "交棒流動性需求" in focus_list:
    suggestions.append(f"以 **{liq_need:,} 萬** 為目標，評估保單與信託作為交棒資金來源的組合比例。")
if "節稅影響" in focus_list:
    suggestions.append("針對贈與／遺產節稅路徑，先做資產分層與移轉時程規劃。")
if "資產配置" in focus_list:
    suggestions.append("以現金流為核心，檢視股權、房產與金融資產的配置與流動性。")
if "保障缺口" in focus_list:
    gap = max(liq_need - int(case.get("insurance_coverage", 0) or 0), 0)
    suggestions.append(f"保障缺口試算約 **{gap:,} 萬**，建議以定期＋終身方案逐步補齊。")
if "股權規劃" in focus_list:
    suggestions.append("盤點股權分散、表決權與經營權安排，必要時搭配家族憲章。")
if "不動產分配" in focus_list:
    suggestions.append("針對主要不動產，先定分配原則與流動性因應，避免繼承爭議。")
if "慈善安排" in focus_list:
    suggestions.append("如有慈善意向，可評估專戶或專款信託，兼顧影響力與稅務。")
if "現金流穩定" in focus_list:
    suggestions.append("建立家族現金流模型，確保傳承前後的支出穩定度。")

if suggestions:
    for s in suggestions:
        st.write(f"- {s}")
else:
    st.caption("（請回上一頁勾選關注重點，可獲得更貼合的建議摘要）")

st.markdown("---")

# ---------- CTA 區塊 ----------
cta1, cta2 = st.columns([1,1])

with cta1:
    if st.button("🔁 返回診斷", use_container_width=True):
        safe_switch("pages/2_Diagnostic.py", "返回診斷")

with cta2:
    if st.button("📅 預約 30 分鐘會談", type="primary", use_container_width=True):
        # 將資料打包給預約頁（5_Booking.py 會讀 booking_prefill）
        st.session_state["booking_prefill"] = {
            "case_id": case_id,
            "name": name,
            "email": email,
            "mobile": mobile,
            "need": f"重點關注：{focus_str}；交棒流動性需求約 {liq_need:,} 萬",
        }
        # 同步給舊流程相容的 user_data（5 頁也會讀）
        st.session_state.setdefault("user_data", {})
        st.session_state["user_data"].update({
            "name": name, "email": email, "phone": mobile
        })
        safe_switch("pages/5_Booking.py", "前往預約頁")

st.markdown("</div>", unsafe_allow_html=True)

# ---- 頁尾 ----
footer()
