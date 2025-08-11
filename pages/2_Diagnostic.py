import streamlit as st
from utils import calculate_estate_tax, calculate_gift_tax, format_wan

st.set_page_config(page_title="傳承策略診斷", page_icon="💡", layout="wide")

st.title("📊 傳承策略診斷")
st.write("請輸入您的資產狀況，系統將協助診斷可能的稅務負擔與傳承現金壓力。所有金額以「萬元」顯示。")

# === 輸入區 ===
with st.form("diagnostic_form"):
    col1, col2 = st.columns(2)
    with col1:
        total_assets = st.number_input("總資產金額（元）", min_value=0.0, step=1_000_000.0, value=100_000_000.0, format="%.0f")
        debt = st.number_input("負債金額（元）", min_value=0.0, step=1_000_000.0, value=0.0, format="%.0f")
    with col2:
        spouse_count = st.number_input("配偶人數（0或1）", min_value=0, max_value=1, step=1, value=1)
        dependent_count = st.number_input("受扶養親屬人數（人）", min_value=0, step=1, value=2)

    # （可選）快速試算贈與稅
    gift_amount = st.number_input("（可選）本年預計贈與金額（元）", min_value=0.0, step=1_000_000.0, value=0.0, format="%.0f")

    submitted = st.form_submit_button("開始診斷")

# === 計算與顯示 ===
if submitted:
    net_assets = float(total_assets) - float(debt)
    estate_tax = calculate_estate_tax(net_assets, spouse_count, dependent_count)

    st.subheader("診斷結果")
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("總資產", format_wan(total_assets, 1))
    c2.metric("負債", format_wan(debt, 1))
    c3.metric("淨資產", format_wan(net_assets, 1))
    c4.metric("估算遺產稅", format_wan(estate_tax, 1))

    # 贈與稅（若有輸入）
    if gift_amount and gift_amount > 0:
        gift_tax = calculate_gift_tax(gift_amount)
        st.info(f"贈與稅試算：{format_wan(gift_tax, 1)}（以年免稅額 244 萬與 10%/15%/20% 級距估算）")

    # 提示
    if estate_tax > 0:
        st.warning("⚠️ 建議建立『稅源預留池』（如以保單作為主要稅源預留），降低短期現金壓力與資產拋售風險。")
    else:
        st.success("✅ 目前估算無遺產稅負擔。仍建議備妥傳承文件（遺囑、醫療意願/代理、受益人與信託條款）。")

st.caption("＊本頁計算為教育性質示意，不構成保險、法律或稅務建議；實務規劃需由專業顧問審閱。")
