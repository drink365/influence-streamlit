# pages/3_Result.py
from pathlib import Path
from zoneinfo import ZoneInfo
import math, csv
import streamlit as st

from src.ui.footer import footer
from src.ui.theme import inject_css
from src.config import DATA_DIR

st.set_page_config(page_title="診斷結果", page_icon="📊", layout="wide")
inject_css()

TPE = ZoneInfo("Asia/Taipei")

# ---------- 工具 ----------
def to_num(x, default=0.0):
    try:
        if x is None: return default
        if isinstance(x, (int, float)): return float(x)
        s = str(x).replace(",", "").strip()
        if s == "": return default
        return float(s)
    except Exception:
        return default

def fmt_num(x, unit="萬"):
    try:
        v = float(x)
        if math.isnan(v) or v <= 0: return "—"
        return f"{v:,.0f} {unit}"
    except Exception:
        return "—"

def band(low, high, unit="萬"):
    l, h = to_num(low), to_num(high)
    if l <= 0 and h <= 0: return "—"
    return f"{fmt_num(l, unit)} – {fmt_num(h, unit)}"

def latest_case_from_csv():
    path = Path(DATA_DIR) / "cases.csv"
    if not path.exists(): 
        return None
    try:
        with path.open("r", encoding="utf-8", newline="") as f:
            rows = list(csv.DictReader(f))
        return rows[-1] if rows else None
    except Exception:
        return None

# ---------- 取得個案（一次性旗標 → session → CSV 最新） ----------
Path(DATA_DIR).mkdir(parents=True, exist_ok=True)

case_id = st.session_state.pop("__go_result_case", None) or st.session_state.get("last_case_id")
case = None

if case_id:
    path = Path(DATA_DIR) / "cases.csv"
    if path.exists():
        try:
            with path.open("r", encoding="utf-8", newline="") as f:
                for row in csv.DictReader(f):
                    if row.get("case_id") == case_id:
                        case = row
                        break
        except Exception:
            case = None

if not case:
    case = latest_case_from_csv()
    case_id = case.get("case_id") if case else None
    if case_id:
        st.session_state["last_case_id"] = case_id

st.title("診斷結果")

if not case:
    st.warning("尚未取得個案資料。請先完成診斷。")
    if st.button("前往診斷", use_container_width=True):
        st.switch_page("pages/2_Diagnostic.py")
    footer(); st.stop()

# ---------- 數值抽取（安全轉型 + 合理 fallback） ----------
equity        = to_num(case.get("equity"))
real_estate   = to_num(case.get("real_estate"))
financial     = to_num(case.get("financial"))
insurance_cov = to_num(case.get("insurance_cov"))

# 優先讀 total_assets；如果 <=0，就用四項資產相加
total_assets  = to_num(case.get("total_assets"))
if total_assets <= 0:
    total_assets = equity + real_estate + financial + insurance_cov

# 流動性需求（預設 5~10%）
liq_low_calc  = total_assets * 0.05
liq_high_calc = total_assets * 0.10

# 若 CSV 沒寫 liq_low/liq_high，就用預設計算
liq_low  = to_num(case.get("liq_low", liq_low_calc))
liq_high = to_num(case.get("liq_high", liq_high_calc))

gap = max(liq_high - insurance_cov, 0)

# ---------- 樣式 ----------
st.markdown(
    """
<style>
  .yc-card { background:#fff; border-radius:16px; padding:18px;
             border:1px solid rgba(0,0,0,.06); box-shadow:0 6px 22px rgba(0,0,0,.05); }
  .yc-hero { background:linear-gradient(180deg,#F7F7F8 0%,#FFF 100%);
             border-radius:20px; padding:24px 28px; }
  .yc-badge { display:inline-block; padding:6px 10px; border-radius:999px;
              background:rgba(168,135,22,0.14); color:#A88716; font-size:12px; font-weight:700;
              border:1px solid rgba(168,135,22,0.27); }
</style>
""",
    unsafe_allow_html=True,
)

# ---------- Hero ----------
st.markdown('<div class="yc-hero">', unsafe_allow_html=True)
st.markdown('<span class="yc-badge">診斷摘要</span>', unsafe_allow_html=True)
st.subheader(f"{case.get('name','—')} 的傳承重點")
st.caption(f"個案編號：{case_id or '—'} ｜ 建立時間：{case.get('ts','—')}")
st.markdown("</div>", unsafe_allow_html=True)

st.markdown("<div style='height:12px'></div>", unsafe_allow_html=True)

# ---------- 左右兩欄 ----------
c1, c2 = st.columns(2)

with c1:
    st.markdown('<div class="yc-card">', unsafe_allow_html=True)
    st.markdown("#### 1) 資產概覽（萬元）")
    st.write(f"- 公司股權：**{fmt_num(equity)}**")
    st.write(f"- 不動產：**{fmt_num(real_estate)}**")
    st.write(f"- 金融資產：**{fmt_num(financial)}**")
    st.write(f"- 既有保單保額：**{fmt_num(insurance_cov)}**")
    st.write("---")
    st.write(f"**合計**：{fmt_num(total_assets)}")
    st.markdown("</div>", unsafe_allow_html=True)

with c2:
    st.markdown('<div class="yc-card">', unsafe_allow_html=True)
    st.markdown("#### 2) 初步建議")
    st.write(f"- 交棒流動性需求（估）：**{band(liq_low, liq_high)}**")
    st.write(f"- 當前保障缺口（參考）：**{fmt_num(gap)}**")
    focuses = (case.get("focus") or "").strip()
    if focuses:
        st.write(f"- 您的重點關注：**{focuses}**")
    st.markdown("</div>", unsafe_allow_html=True)

st.markdown("<div style='height:12px'></div>", unsafe_allow_html=True)

# ---------- 下一步 + 返回修改 ----------
st.markdown('<div class="yc-card">', unsafe_allow_html=True)
st.markdown("### 下一步")
st.markdown(
    """
- 若交棒時程在 **3 年內**，建議優先規劃 **流動性來源**（現金／信用額度／保單現金價值／資產重整）、**節稅與合規文件**（遺囑、信託、股權安排）。
- 若保障缺口大於 0，可評估以 **風險保障** 或 **資產配置** 補強，降低家族現金流風險。
- 若您需要進一步的落地方案，我們可在 30 分鐘會談中依您的目標提供具體路徑與時程。
    """
)
cta1, cta2, cta3 = st.columns([1,1,1])
with cta1:
    if st.button("🔁 返回修改", use_container_width=True):
        # 回填診斷頁所有欄位到 session_state
        st.session_state["diag_name"]   = case.get("name","")
        st.session_state["diag_email"]  = case.get("email","")
        st.session_state["diag_mobile"] = case.get("mobile","")
        st.session_state["diag_marital"] = case.get("marital","未婚")
        try:
            st.session_state["diag_children"] = int(float(case.get("children",0)))
        except Exception:
            st.session_state["diag_children"] = 0
        st.session_state["diag_heirs"] = case.get("heirs_ready","尚未明確")

        # 數字欄位
        st.session_state["diag_equity"] = to_num(case.get("equity"), 0)
        st.session_state["diag_re"]     = to_num(case.get("real_estate"), 0)
        st.session_state["diag_fin"]    = to_num(case.get("financial"), 0)
        st.session_state["diag_cov"]    = to_num(case.get("insurance_cov"), 0)

        # 多選與 slider
        focuses = (case.get("focus") or "").strip()
        st.session_state["diag_focus"] = focuses.split("、") if focuses else []
        try:
            st.session_state["diag_years"] = int(float(case.get("target_years", 3)))
        except Exception:
            st.session_state["diag_years"] = 3

        # 同意勾選預設為 True
        st.session_state["diag_agree"] = True

        st.switch_page("pages/2_Diagnostic.py")

with cta2:
    if st.button("📅 預約 30 分鐘會談", type="primary", use_container_width=True):
        st.switch_page("pages/5_Booking.py")
with cta3:
    if st.button("🏠 回首頁", use_container_width=True):
        st.switch_page("app.py")
st.markdown("</div>", unsafe_allow_html=True)

footer()
