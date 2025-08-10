# pages/3_Result.py
from pathlib import Path
from zoneinfo import ZoneInfo
import math, csv

import streamlit as st

from src.ui.footer import footer
from src.ui.theme import inject_css
from src.repos.cases import CaseRepo
from src.config import DATA_DIR

st.set_page_config(page_title="診斷結果", page_icon="📊", layout="wide")
inject_css()

PRIMARY = "#BD0E1B"
ACCENT  = "#A88716"
INK     = "#3C3F46"
BG_SOFT = "#F7F7F8"
TPE = ZoneInfo("Asia/Taipei")

# ---------- 小工具 ----------
def to_num(x, default=0):
    """把輸入轉為 float；失敗回 default。"""
    try:
        if x is None:
            return default
        if isinstance(x, (int, float)):
            return float(x)
        s = str(x).replace(",", "").strip()
        if s == "":
            return default
        return float(s)
    except Exception:
        return default

def fmt_num(x, unit="萬"):
    """千分位；非正數顯示 '—'。"""
    try:
        v = float(x)
        if math.isnan(v) or v <= 0:
            return "—"
        return f"{v:,.0f} {unit}"
    except Exception:
        return "—"

def band(low, high, unit="萬"):
    """區間字串；任一端無效則顯示 '—'。"""
    if (low is None and high is None) or (to_num(low) <= 0 and to_num(high) <= 0):
        return "—"
    return f"{fmt_num(low, unit)} – {fmt_num(high, unit)}"

def latest_case_from_csv():
    """讀 data/cases.csv，回傳最後一筆 dict。"""
    path = Path(DATA_DIR) / "cases.csv"
    if not path.exists():
        return None
    try:
        with path.open("r", encoding="utf-8", newline="") as f:
            rows = list(csv.DictReader(f))
        return rows[-1] if rows else None
    except Exception:
        return None

# ---------- 讀取個案（session -> CSV 最新 -> 提示） ----------
Path(DATA_DIR).mkdir(parents=True, exist_ok=True)
repo = CaseRepo()

case_id = st.session_state.get("last_case_id")
case = repo.get_by_case_id(case_id) if case_id else None

if not case:
    case = latest_case_from_csv()
    case_id = case.get("case_id") if case else None
    if case_id:
        st.session_state["last_case_id"] = case_id  # 補寫回 session

st.title("診斷結果")

if not case:
    st.warning("尚未取得個案資料。請先完成診斷。")
    if st.button("前往診斷", use_container_width=True):
        st.switch_page("pages/2_Diagnostic.py")
    footer(); st.stop()

# ---------- 抽取並健壯化數值 ----------
equity        = to_num(case.get("equity"))
real_estate   = to_num(case.get("real_estate"))
financial     = to_num(case.get("financial"))
insurance_cov = to_num(case.get("insurance_cov"))
total_assets  = to_num(case.get("total_assets", equity + real_estate + financial + insurance_cov))

# 預設試算：總資產 5%~10% 作為交棒流動性緩衝（示意）
liq_low_calc  = total_assets * 0.05
liq_high_calc = total_assets * 0.10
liq_low  = to_num(case.get("liq_low", liq_low_calc))
liq_high = to_num(case.get("liq_high", liq_high_calc))
gap = max(liq_high - insurance_cov, 0)

# ---------- 樣式 ----------
st.markdown(f"""
<style>
  .yc-card {{
    background:#fff; border-radius:16px; padding:18px 18px;
    border:1px solid rgba(0,0,0,.06); box-shadow:0 6px 22px rgba(0,0,0,.05);
  }}
  .yc-hero {{ background:linear-gradient(180deg,{BG_SOFT} 0%,#FFF 100%); border-radius:20px; padding:24px 28px; }}
  .yc-badge {{ display:inline-block; padding:6px 10px; border-radius:999px; background:{ACCENT}14; color:{ACCENT}; font-size:12px; font-weight:700; border:1px solid {ACCENT}44; }}
</style>
""", unsafe_allow_html=True)

# ---------- Hero 區 ----------
st.markdown('<div class="yc-hero">', unsafe_allow_html=True)
st.markdown('<span class="yc-badge">診斷摘要</span>', unsafe_allow_html=True)
st.subheader(f"{case.get('name','—')} 的傳承重點")
st.caption(f"個案編號：{case_id or '—'} ｜ 建立時間：{case.get('ts','—')}")
st.markdown("</div>", unsafe_allow_html=True)

st.markdown("<div style='height:12px'></div>", unsafe_allow_html=True)

# ---------- 左右兩欄 ----------
col1, col2 = st.columns(2)

with col1:
    st.markdown('<div class="yc-card">', unsafe_allow_html=True)
    st.markdown("#### 1) 資產概覽（萬元）")
    st.write(f"- 公司股權：**{fmt_num(equity)}**")
    st.write(f"- 不動產：**{fmt_num(real_estate)}**")
    st.write(f"- 金融資產：**{fmt_num(financial)}**")
    st.write(f"- 既有保單保額：**{fmt_num(insurance_cov)}**")
    st.write("---")
    st.write(f"**合計**：{fmt_num(total_assets)}")
    st.markdown("</div>", unsafe_allow_html=True)

with col2:
    st.markdown('<div class="yc-card">', unsafe_allow_html=True)
    st.markdown("#### 2) 初步建議")
    st.write(f"- 交棒流動性需求（估）：**{band(liq_low, liq_high)}**")
    st.write(f"- 當前保障缺口（參考）：**{fmt_num(gap)}**")
    focuses = (case.get("focus") or "").strip()
    if focuses:
        st.write(f"- 您的重點關注：**{focuses}**")
    st.markdown("</div>", unsafe_allow_html=True)

st.markdown("<div style='height:12px'></div>", unsafe_allow_html=True)

# ---------- 下一步 ----------
st.markdown('<div class="yc-card">', unsafe_allow_html=True)
st.markdown("### 下一步")
st.markdown(
    """
- 若交棒時程在 **3 年內**，建議優先規劃 **流動性來源**（現金／信用額度／保單現金價值／資產重整）、**節稅與合規文件**（遺囑、信託、股權安排）。
- 若保障缺口大於 0，可評估以 **風險保障** 或 **資產配置** 補強，降低家族現金流風險。
- 若您需要進一步的落地方案，我們可在 30 分鐘會談中依您的目標提供具體路徑與時程。
    """
)
cta1, cta2 = st.columns([1,1])
with cta1:
    if st.button("預約 30 分鐘會談", type="primary", use_container_width=True):
        st.switch_page("pages/5_Booking.py")
with cta2:
    if st.button("回首頁", use_container_width=True):
        st.switch_page("app.py")
st.markdown("</div>", unsafe_allow_html=True)

footer()
