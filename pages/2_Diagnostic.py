# pages/2_Diagnostic.py
import streamlit as st
from src.domain.tax_loader import load_tax_constants
from src.domain.tax_rules import EstateTaxCalculator

st.set_page_config(page_title="遺產稅診斷", page_icon="💡", layout="wide")

st.title("📊 遺產稅診斷（單位：萬元）")
st.caption("本頁專注遺產稅估算；免稅額、常用扣除額與喪葬費依現行稅則自動套用。")

def fmt_wan(x: float) -> str:
    return f"{float(x):,.1f} 萬元"

def _tax_from_brackets_wan(taxable_base_wan: float, constants) -> float:
    """用稅率級距回推（自動判斷萬/元），回傳『萬』。"""
    # 先找萬級距
    brackets = getattr(constants, "ESTATE_TAX_BRACKETS_WAN", None) \
        or getattr(constants, "ESTATE_TAX_THRESHOLDS_WAN", None)
    if brackets:
        tax_wan, last = 0.0, 0.0
        for limit, rate in brackets:
            if limit == float("inf") or taxable_base_wan <= limit:
                tax_wan += (taxable_base_wan - last) * rate
                break
            tax_wan += (limit - last) * rate
            last = limit
        return max(0.0, tax_wan)

    # 再試元級距
    brackets_yuan = getattr(constants, "ESTATE_TAX_THRESHOLDS", None)
    unit = getattr(constants, "UNIT_FACTOR", 10000)
    if brackets_yuan:
        base_yuan = float(taxable_base_wan) * unit
        tax_yuan, last = 0.0, 0.0
        for limit, rate in brackets_yuan:
            if limit == float("inf") or base_yuan <= limit:
                tax_yuan += (base_yuan - last) * rate
                break
            tax_yuan += (limit - last) * rate
            last = limit
        return max(0.0, tax_yuan / unit)

    return 0.0

def _compute_tax_wan_robust(calc: EstateTaxCalculator, constants, taxable_base_wan: float) -> float:
    """優先用吃『萬』的方法；沒有就轉『元』；最後用級距回推。回傳『萬』。"""
    # A. 萬為單位的方法
    for name in ("compute_tax_wan", "compute_estate_tax_wan", "tax_wan_from_base"):
        if hasattr(calc, name):
            try:
                return float(getattr(calc, name)(float(taxable_base_wan)))
            except Exception:
                pass
    # B. 元為單位的方法（自動換算）
    unit = getattr(constants, "UNIT_FACTOR", 10000)
    base_yuan = float(taxable_base_wan) * unit
    for name in ("compute_tax", "compute_estate_tax", "tax_from_base"):
        if hasattr(calc, name):
            try:
                tax_yuan = float(getattr(calc, name)(base_yuan))
                return tax_yuan / unit
            except Exception:
                pass
    # C. 回退：用級距
    return _tax_from_brackets_wan(taxable_base_wan, constants)

# === 第一排：總資產 / 總負債（萬元） ===
with st.form("estate_form"):
    r1c1, r1c2 = st.columns(2)
    with r1c1:
        total_assets_wan = st.number_input("總資產（萬元）", min_value=0.0, step=10.0, value=10000.0, format="%.1f")
    with r1c2:
        total_liabilities_wan = st.number_input("總負債（萬元）", min_value=0.0, step=10.0, value=0.0, format="%.1f")

    st.divider()
    # === 第二排：家庭成員 ===
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
    # 1) 淨遺產（萬）
    net_estate_wan = max(0.0, float(total_assets_wan) - float(total_liabilities_wan))

    # 2) 稅則與計算器
    constants = load_tax_constants()
    calc = EstateTaxCalculator(constants)

    # 3) 合計扣除額（萬）
    deductions_wan = calc.compute_total_deductions_wan(
        has_spouse=bool(has_spouse),
        adult_children=int(adult_children),
        parents=int(parents),
        disabled_people=int(disabled_people),
        other_dependents=int(other_dependents),
    )

    # 4) 課稅基礎（萬）
    taxable_base_wan = calc.compute_taxable_base_wan(
        net_estate_wan=float(net_estate_wan),
        total_deductions_wan=float(deductions_wan),
    )

    # 5) 遺產稅（萬）— 修正單位誤差，避免出現 0
    tax_wan = _compute_tax_wan_robust(calc, constants, float(taxable_base_wan))

    # === 顯示 ===
    st.subheader("計算結果（單位：萬元）")
    m1, m2, m3, m4 = st.columns(4)
    m1.metric("淨遺產", fmt_wan(net_estate_wan))
    m2.metric("合計扣除額", fmt_wan(deductions_wan))
    m3.metric("課稅基礎", fmt_wan(taxable_base_wan))
    m4.metric("估算遺產稅", fmt_wan(tax_wan))

    st.caption("＊扣除額包含：基本扣除、配偶/受扶養扣除與喪葬費等；依現行稅則自動判定。")

st.caption("＊本頁為教育性質示意，不構成保險、法律或稅務建議；正式申報請依主管機關規定與完整文件。")
