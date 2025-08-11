import streamlit as st
import pandas as pd
from utils import calculate_estate_tax, calculate_gift_tax

st.set_page_config(page_title="傳承策略診斷", page_icon="💡", layout="wide")

st.title("📊 傳承策略診斷")

st.write("請輸入您的資產狀況，系統將協助診斷可能的稅務負擔與傳承風險。")

# 輸入欄位
with st.form("diagnostic_form"):
    col1, col2 = st.columns(2)
    with col1:
        total_assets = st.number_input("總資產金額（元）", min_value=0, step=1000000, value=100000000)
        debt = st.number_input("負債金額（元）", min_value=0, step=1000000, value=0)
    with col2:
        spouse_count = st.number_input("配偶人數", min_value=0, max_value=1, step=1, value=1)
        dependent_count = st.number_input("受扶養親屬人數", min_value=0, step=1, value=2)

    submitted = st.form_submit_button("開始診斷")

if submitted:
    taxable_base = total_assets - debt
    estate_tax = calculate_estate_tax(taxable_base, spouse_count, dependent_count)

    st.subheader("診斷結果")
    st.write(f"💰 **總資產：** {total_assets/10000:,.1f} 萬元")
    st.write(f"💳 **負債：** {debt/10000:,.1f} 萬元")
    st.write(f"📉 **淨資產：** {taxable_base/10000:,.1f} 萬元")
    st.write(f"🏛️ **估算遺產稅：** {estate_tax/10000:,.1f} 萬元")

    # 提示
    if estate_tax > 0:
        st.warning("⚠️ 建議提前進行資產配置與保單規劃，以降低稅務衝擊。")
    else:
        st.success("✅ 目前免稅額足夠，暫無遺產稅負擔。")
