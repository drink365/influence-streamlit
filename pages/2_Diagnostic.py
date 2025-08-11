import streamlit as st
from utils import calculate_estate_tax, calculate_gift_tax

st.set_page_config(page_title="傳承策略診斷", page_icon="💡", layout="wide")

st.title("📊 傳承策略診斷（以「萬元」為單位）")
st.write("請輸入資產與負債（單位：萬元），系統將估算可能的遺產稅與現金壓力。")

# 小工具：格式化為「萬元」
def fmt_wan(x: float) -> str:
    return f"{x:,.1f} 萬元"

# === 輸入區（全部以「萬元」為單位） ===
with st.form("diagnostic_form"):
    col1, col2 = st.columns(2)
    with col1:
        total_assets_wan = st.number_input("總資產（萬元）", min_value=0.0, step=10.0, value=10000.0, format="%.1f")
        debt_wan = st.number_input("負債（萬元）", min_value=0.0, step=10.0, value=0.0, format="%.1f")
    with col2:
        spouse_count = st.number_input("配偶人數（0或1）", min_value=0, max_value=1, step=1, value=1)
        dependent_count = st.number_input("受扶養親屬人數（人）", min_value=0, step=1, value=2)

    # 可選：本年贈與金額（萬元）
    gift_amount_wan = st.number_input("（可選）本年預計贈與金額（萬元）", min_value=0.0, step=10.0, value=0.0, format="%.1f")

    submitted = st.form_submit_button("開始診斷")

# === 計算與顯示（內部換算成「元」計算，顯示回到「萬元」） ===
if submitted:
    # 換算成元
    total_assets = total_assets_wan * 10_000
    debt = debt_wan * 10_000
    net_assets = total_assets - debt

    # 遺產稅（元）
    estate_tax = calculate_estate_tax(
        taxable_base=net_assets,
        spouse_count=spouse_count,
        dependent_count=dependent_count
    )
    estate_tax_wan = estate_tax / 10_000

    # 顯示（萬元）
    st.subheader("診斷結果（萬元）")
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("總資產", fmt_wan(total_assets_wan))
    c2.metric("負債", fmt_wan(debt_wan))
    c3.metric("淨資產", fmt_wan(total_assets_wan - debt_wan))
    c4.metric("估算遺產稅", fmt_wan(estate_tax_wan))

    # 贈與稅（若有輸入）
    if gift_amount_wan and gift_amount_wan > 0:
        gift_tax = calculate_gift_tax(gift_amount_wan * 10_000)   # 先轉元計算
        gift_tax_wan = gift_tax / 10_000
        st.info(f"贈與稅試算：{fmt_wan(gift_tax_wan)}（以年免稅額 244 萬與 10%/15%/20% 級距估算）")

    # 提示
    if estate_tax > 0:
        st.warning("⚠️ 建議建立『稅源預留池』（例如以保單作為主要稅源預留），降低短期現金壓力與資產拋售風險。")
    else:
        st.success("✅ 目前估算無遺產稅負擔。仍建議備妥傳承文件（遺囑、醫療意願/代理、受益人與信託條款）。")

st.caption("＊本頁計算為教育性質示意，不構成保險、法律或稅務建議；實務規劃需由專業顧問審閱。")
