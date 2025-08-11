# pages/2_Diagnostic.py
import streamlit as st
from datetime import date

# 直接用你既有的「精準稅則」模組
from src.domain.tax_loader import load_tax_constants
from src.domain.tax_rules import EstateTaxCalculator

st.set_page_config(page_title="遺產稅診斷", page_icon="💡", layout="wide")

st.title("📊 遺產稅診斷（輸入/顯示皆為「萬元」）")
st.caption("本頁僅專注遺產稅估算；免稅額、常用扣除額與喪葬費依你既有稅則自動套用。")

def fmt_wan(x: float) -> str:
    return f"{float(x):,.1f} 萬元"

# === 參數（稅則版本日期，可改今天）===
with st.expander("進階設定", expanded=False):
    rules_date = st.date_input("稅則適用日期", value=date.today(), format="YYYY-MM-DD")
    st.caption("若未來稅則更新，改此日期即可套用對應版本。")

# === 輸入（全部以「萬元」）===
with st.form("estate_form"):
    c1, c2 = st.columns(2)
    with c1:
        net_estate_wan = st.number_input("淨遺產（萬元）", min_value=0.0, step=10.0, value=10_000.0, format="%.1f",
                                          help="已扣除負債後之淨額；本頁僅做遺產稅估算，不再細拆資產/負債明細。")
        has_spouse = st.checkbox("有配偶", value=True)
        parents = st.number_input("直系尊親屬（父母/祖父母）人數", min_value=0, step=1, value=0)
    with c2:
        adult_children = st.number_input("成年子女人數", min_value=0, step=1, value=2)
        disabled_people = st.number_input("身心障礙受扶養人數", min_value=0, step=1, value=0)
        other_dependents = st.number_input("其他受扶養親屬人數", min_value=0, step=1, value=0)

    submitted = st.form_submit_button("開始計算")

# === 計算（內部以「萬」單位對應你的稅則模組；不做元↔萬來回換算，避免誤差）===
if submitted:
    # 載入對應日期的稅則常數
    constants = load_tax_constants(on_date=rules_date)

    # 初始化你的計算器（你現有程式已實作）
    calc = EstateTaxCalculator(constants)

    # 家庭結構參數（沿用你現有方法簽名）
    ded_wan = calc.compute_total_deductions_wan(
        has_spouse=bool(has_spouse),
        adult_children=int(adult_children),
        parents=int(parents),
        disabled_people=int(disabled_people),
        other_dependents=int(other_dependents),
    )
    # 課稅基礎（萬）
    taxable_base_wan = calc.compute_taxable_base_wan(
        net_estate_wan=float(net_estate_wan),
        total_deductions_wan=float(ded_wan),
    )
    # 遺產稅（萬）
    tax_wan = calc.compute_tax_wan(float(taxable_base_wan))

    # === 顯示（萬元，保留 1 位小數）===
    st.subheader("計算結果（單位：萬元）")
    m1, m2, m3 = st.columns(3)
    m1.metric("淨遺產", fmt_wan(net_estate_wan))
    m2.metric("合計扣除額", fmt_wan(ded_wan))
    m3.metric("課稅基礎", fmt_wan(taxable_base_wan))

    st.metric("估算遺產稅額", fmt_wan(tax_wan))

    st.info("說明：扣除額已含基本扣除、配偶/受扶養親屬扣除與喪葬費等依規定可扣項；數值由你現有稅則模組自動判定。")

st.caption("＊本頁為教育性質示意，不構成保險、法律或稅務建議；正式申報仍須以主管機關規定與完整文件為準。")
