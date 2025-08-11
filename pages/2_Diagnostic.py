# pages/2_Diagnostic.py
# 單位一律「萬元」，依正式規則（你提供的 estate_tax_app.py）計算

import streamlit as st
from math import inf

st.set_page_config(page_title="遺產稅診斷", page_icon="💡", layout="wide")

# ===== 正式規則常數（單位：萬元） =====
EXEMPT_AMOUNT = 1333.0   # 免稅額
FUNERAL_EXPENSE = 138.0  # 喪葬費

SPOUSE_DEDUCTION_VALUE = 553.0       # 配偶扣除（一次）
ADULT_CHILD_DEDUCTION = 56.0          # 子女（每人）
PARENTS_DEDUCTION = 138.0             # 父母（每人）
DISABLED_DEDUCTION = 693.0            # 重度身心障礙（每人）
OTHER_DEPENDENTS_DEDUCTION = 56.0     # 其他受扶養（每人）

# 累進級距（上限：萬元；稅率）
TAX_BRACKETS = [
    (5621.0, 0.10),
    (11242.0, 0.15),
    (inf,    0.20),
]

def fmt_wan(x: float) -> str:
    return f"{float(x):,.1f} 萬元"

def compute_total_deductions_wan(
    has_spouse: bool,
    adult_children: int,
    parents: int,
    disabled_people: int,
    other_dependents: int,
) -> float:
    """總扣除額（萬）＝喪葬＋（有配偶則配偶扣除）＋子女×56＋父母×138＋障礙×693＋其他×56"""
    dependents_total = (
        max(0, int(adult_children)) * ADULT_CHILD_DEDUCTION
        + max(0, int(parents)) * PARENTS_DEDUCTION
        + max(0, int(disabled_people)) * DISABLED_DEDUCTION
        + max(0, int(other_dependents)) * OTHER_DEPENDENTS_DEDUCTION
    )
    return float(FUNERAL_EXPENSE + (SPOUSE_DEDUCTION_VALUE if has_spouse else 0.0) + dependents_total)

def progressive_tax_wan(taxable_base_wan: float) -> float:
    """依 TAX_BRACKETS（萬）計算累進稅額，回傳『萬』"""
    if taxable_base_wan <= 0:
        return 0.0
    tax = 0.0
    last = 0.0
    for limit, rate in TAX_BRACKETS:
        if limit == inf or taxable_base_wan <= limit:
            tax += (taxable_base_wan - last) * rate
            break
        tax += (limit - last) * rate
        last = limit
    return max(0.0, tax)

# ===== 介面 =====
st.title("📊 遺產稅診斷（單位：萬元）")
st.caption("依正式規則計算：免稅額、喪葬費、配偶與各類受扶養扣除皆已內建；級距為 10% / 15% / 20%。")

with st.form("estate_form"):
    # 第一排：資產 / 負債
    a1, a2 = st.columns(2)
    with a1:
        total_assets_wan = st.number_input("總資產（萬元）", min_value=0.0, step=10.0, value=10_000.0, format="%.1f")
    with a2:
        total_liabilities_wan = st.number_input("總負債（萬元）", min_value=0.0, step=10.0, value=0.0, format="%.1f")

    st.divider()

    # 第二排：家庭成員
    b1, b2, b3, b4, b5 = st.columns(5)
    with b1:
        has_spouse = st.checkbox("有配偶", value=True)
    with b2:
        adult_children = st.number_input("成年子女（人）", min_value=0, step=1, value=2)
    with b3:
        parents = st.number_input("直系尊親屬（人）", min_value=0, step=1, value=0)
    with b4:
        disabled_people = st.number_input("重度身心障礙（人）", min_value=0, step=1, value=0)
    with b5:
        other_dependents = st.number_input("其他受扶養（人）", min_value=0, step=1, value=0)

    submitted = st.form_submit_button("開始計算")

if submitted:
    # 淨遺產（萬）
    net_estate_wan = max(0.0, float(total_assets_wan) - float(total_liabilities_wan))

    # 總扣除額（萬）
    total_deductions_wan = compute_total_deductions_wan(
        has_spouse=bool(has_spouse),
        adult_children=int(adult_children),
        parents=int(parents),
        disabled_people=int(disabled_people),
        other_dependents=int(other_dependents),
    )

    # 課稅基礎（萬）＝ max(淨遺產 − 免稅額 − 總扣除額, 0)
    taxable_base_wan = max(0.0, float(net_estate_wan) - EXEMPT_AMOUNT - total_deductions_wan)

    # 累進稅額（萬）
    tax_wan = progressive_tax_wan(taxable_base_wan)

    # 結果
    st.subheader("計算結果（單位：萬元）")
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("淨遺產", fmt_wan(net_estate_wan))
    c2.metric("合計扣除額", fmt_wan(total_deductions_wan))
    c3.metric("課稅基礎", fmt_wan(taxable_base_wan))
    c4.metric("估算遺產稅", fmt_wan(tax_wan))

st.caption("＊本頁為教育性質示意，不構成保險、法律或稅務建議；正式申報請依主管機關規定與完整文件。")
