# pages/2_Diagnostic.py
import streamlit as st

from src.domain.tax_loader import load_tax_constants
from src.domain.tax_rules import EstateTaxCalculator

st.set_page_config(page_title="遺產稅診斷", page_icon="💡", layout="wide")

st.title("📊 遺產稅診斷（單位：萬元）")
st.caption("本頁僅專注遺產稅估算；免稅額、常用扣除額與喪葬費依現行稅則自動套用。")

def fmt_wan(x: float) -> str:
    return f"{float(x):,.1f} 萬元"

def _progressive_tax_wan_from_constants(taxable_base_wan: float, constants) -> float:
    """
    從 constants 讀級距（以「萬」為單位的上限＋稅率）計算稅額（回傳單位：萬）。
    會嘗試以下欄位名稱（擇一存在即可）：
      - ESTATE_TAX_BRACKETS_WAN
      - ESTATE_TAX_THRESHOLDS_WAN
      - ESTATE_TAX_THRESHOLDS  （若為元，且偵測到 UNIT_FACTOR，會自動轉成萬）
    """
    # 取得 brackets
    brackets = getattr(constants, "ESTATE_TAX_BRACKETS_WAN", None) \
        or getattr(constants, "ESTATE_TAX_THRESHOLDS_WAN", None) \
        or getattr(constants, "ESTATE_TAX_THRESHOLDS", None)

    if not brackets:
        return 0.0

    # 嘗試判斷 brackets 單位（萬 或 元）
    # 若有 UNIT_FACTOR 且看起來像元級距（> 1e6），就換算成萬
    unit_factor = getattr(constants, "UNIT_FACTOR", 10000)  # 常見會是 10000
    norm_brackets = []
    for limit, rate in brackets:
        if limit == float("inf"):
            norm_brackets.append((limit, rate))
        else:
            # 估測：如果上限大於 1,000,000，視為元，轉萬；否則直接沿用（本來就是萬）
            limit_wan = limit / unit_factor if limit and limit > 1_000_000 else limit
            norm_brackets.append((limit_wan, rate))

    # 累進計算（單位：萬）
    if taxable_base_wan <= 0:
        return 0.0
    tax_wan, last = 0.0, 0.0
    for limit, rate in norm_brackets:
        if taxable_base_wan > limit:
            if limit == float("inf"):
                # 無窮上限直接全部套
                tax_wan += (taxable_base_wan - last) * rate
                break
            tax_wan += (limit - last) * rate
            last = limit
        else:
            tax_wan += (taxable_base_wan - last) * rate
            break
    return max(0.0, tax_wan)

def _compute_tax_wan_safe(calc: EstateTaxCalculator, taxable_base_wan: float, constants) -> float:
    """
    安全呼叫：優先用 Calculator 內建方法；若不存在則用級距回推。
    回傳單位：萬
    """
    # 可能的命名（依你專案而定）
    for attr in ["compute_tax_wan", "compute_estate_tax_wan", "tax_wan_from_base"]:
        if hasattr(calc, attr):
            try:
                return float(getattr(calc, attr)(float(taxable_base_wan)))
            except Exception:
                pass
    # 回退：用級距自行計
    return _progressive_tax_wan_from_constants(float(taxable_base_wan), constants)

# === 第一排：資產/負債（萬元） ===
with st.form("estate_form"):
    r1c1, r1c2 = st.columns(2)
    with r1c1:
        net_assets_input_mode = st.radio(
            "輸入方式",
            ["我只輸入『淨遺產』", "我分開輸入『總資產＋總負債』"],
            index=1,
            horizontal=True
        )
    with r1c2:
        pass

    if net_assets_input_mode == "我分開輸入『總資產＋總負債』":
        c1, c2 = st.columns(2)
        with c1:
            total_assets_wan = st.number_input("總資產（萬元）", min_value=0.0, step=10.0, value=10000.0, format="%.1f")
        with c2:
            total_liabilities_wan = st.number_input("總負債（萬元）", min_value=0.0, step=10.0, value=0.0, format="%.1f")
        net_estate_wan = max(0.0, float(total_assets_wan) - float(total_liabilities_wan))
    else:
        net_estate_wan = st.number_input("淨遺產（萬元）", min_value=0.0, step=10.0, value=10000.0, format="%.1f")

    st.divider()
    # === 第二排：家庭成員狀況 ===
    f1, f2, f3, f4, f5 = st.columns(5)
    with f1:
        has_spouse = st.checkbox("有配偶", value=True)
    with f2:
        adult_children = st.number_input("成年子女（人）", min_value=0, step=1, value=2)
    with f3:
        parents = st.number_input("直系尊親屬（人）", min_value=0, step=1, value=0)
    with f4:
        disabled_people = st.number_input("身心障礙受扶養（人）", min_value=0, step=1, value=0)
    with f5:
        other_dependents = st.number_input("其他受扶養（人）", min_value=0, step=1, value=0)

    submitted = st.form_submit_button("開始計算")

if submitted:
    # 1) 載入稅則與計算器（以你專案現行版本為準）
    constants = load_tax_constants()
    calc = EstateTaxCalculator(constants)

    # 2) 計算合計扣除額（萬）
    deductions_wan = calc.compute_total_deductions_wan(
        has_spouse=bool(has_spouse),
        adult_children=int(adult_children),
        parents=int(parents),
        disabled_people=int(disabled_people),
        other_dependents=int(other_dependents),
    )

    # 3) 課稅基礎（萬）
    taxable_base_wan = calc.compute_taxable_base_wan(
        net_estate_wan=float(net_estate_wan),
        total_deductions_wan=float(deductions_wan),
    )

    # 4) 遺產稅（萬）— 安全呼叫 + 回退
    tax_wan = _compute_tax_wan_safe(calc, float(taxable_base_wan), constants)

    # === 顯示（皆為「萬元」，保留 1 位小數）===
    st.subheader("計算結果（單位：萬元）")
    m1, m2, m3, m4 = st.columns(4)
    m1.metric("淨遺產", fmt_wan(net_estate_wan))
    m2.metric("合計扣除額", fmt_wan(deductions_wan))
    m3.metric("課稅基礎", fmt_wan(taxable_base_wan))
    m4.metric("估算遺產稅", fmt_wan(tax_wan))

    st.caption("＊扣除額已含基本扣除、配偶/受扶養與喪葬費等依規定可扣項；數值由現行稅則自動判定。")

st.caption("＊本頁為教育性質示意，不構成保險、法律或稅務建議；正式申報請依主管機關規定與完整文件。")
