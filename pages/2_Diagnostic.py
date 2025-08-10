# pages/2_Diagnostic.py
import streamlit as st
from datetime import datetime, date
import pytz, uuid

from src.repos.case_repo import CaseRepo
from src.repos.event_repo import EventRepo
from src.domain.tax_rules import EstateTaxCalculator
from src.domain.tax_loader import load_tax_constants

st.set_page_config(page_title="診斷", page_icon="🧮", layout="wide")

st.title("🧮 傳承風險診斷（對齊＋可版本切換）")

# 稅源緩衝倍數（UI 可調）
buffer_mult = st.slider("稅源預留緩衝倍數", 1.00, 1.50, 1.10, 0.01)

with st.form("diag"):
    col1, col2 = st.columns(2)
    with col1:
        client_alias = st.text_input("客戶稱呼", placeholder="例如：李先生")
        assets_financial = st.number_input("金融資產（元）", min_value=0.0, step=100000.0, format="%.0f")
        assets_realestate = st.number_input("不動產市值（元）", min_value=0.0, step=100000.0, format="%.0f")
        assets_business = st.number_input("公司股權估值（元）", min_value=0.0, step=100000.0, format="%.0f")
        liabilities = st.number_input("負債總額（元）", min_value=0.0, step=100000.0, format="%.0f")
    with col2:
        st.markdown("#### 扣除與家庭狀況（對齊 estate 規則）")
        has_spouse = st.toggle("有配偶")
        adult_children = st.number_input("成年子女數（每人 56 萬扣除）", min_value=0, step=1, value=0)
        parents = st.number_input("父母人數（每人 138 萬扣除）", min_value=0, step=1, value=0)
        disabled_people = st.number_input("重度以上身心障礙人數（每人 693 萬）", min_value=0, step=1, value=0)
        other_dependents = st.number_input("其他受扶養者（每人 56 萬）", min_value=0, step=1, value=0)

        st.markdown("#### 隱私與告知")
        agree = st.checkbox("我已閱讀並同意隱私權政策與資料使用說明。")
        st.caption("＊此診斷僅供參考，完整規劃以專業顧問審核為準。")

    submitted = st.form_submit_button("🚀 立即試算", type="primary", disabled=not agree)

if submitted:
    # 淨遺產（元）
    total_assets = assets_financial + assets_realestate + assets_business
    net_estate = max(total_assets - liabilities, 0.0)

    # 依日期載入稅制版本（你也可以改成 version="estate-tax-app-v1" 固定使用）
    constants = load_tax_constants(on_date=date.today())
    calc = EstateTaxCalculator(constants)
    diag = calc.diagnose_yuan(
        net_estate,
        has_spouse=has_spouse,
        adult_children=int(adult_children),
        parents=int(parents),
        disabled_people=int(disabled_people),
        other_dependents=int(other_dependents),
        buffer_multiplier=buffer_mult,
    )

    # 產生 Case ID（台北時區）
    tz = pytz.timezone("Asia/Taipei")
    date_str = datetime.now(tz).strftime("%Y%m%d")
    short = str(uuid.uuid4())[:4].upper()
    case_id = f"CASE-{date_str}-{short}"

    # ✅ 小補丁A：把 taxable_base_wan 寫入 payload，供結果頁圖表使用
    CaseRepo.upsert({
        "id": case_id,
        "advisor_id": st.session_state.get("advisor_id","guest"),
        "advisor_name": st.session_state.get("advisor_name","未登入"),
        "client_alias": client_alias or "未命名",
        "assets_financial": assets_financial,
        "assets_realestate": assets_realestate,
        "assets_business": assets_business,
        "liabilities": liabilities,
        "net_estate": net_estate,
        "tax_estimate": diag["tax_yuan"],
        "liquidity_needed": diag["recommended_liquidity_yuan"],
        "status": "Prospect",
        "payload": {
            "assets_total": total_assets,
            "rules_version": constants.VERSION,
            "unit_factor": constants.UNIT_FACTOR,
            "taxable_base_wan": diag["taxable_base_wan"],
            "params": {
                "has_spouse": has_spouse,
                "adult_children": int(adult_children),
                "parents": int(parents),
                "disabled_people": int(disabled_people),
                "other_dependents": int(other_dependents),
                "buffer_multiplier": float(buffer_mult)
            }
        },
    })
    EventRepo.log(case_id, "DIAG_DONE", {
        "net_estate_yuan": net_estate,
        "taxable_base_wan": diag["taxable_base_wan"],
        "deductions_wan": diag["deductions_wan"],
        "tax_yuan": diag["tax_yuan"],
        "buffer": diag["buffer_multiplier"],
        "version": constants.VERSION
    })

    st.success(f"已完成試算，案件碼：**{case_id}**")
    m1,m2,m3,m4,m5 = st.columns(5)
    m1.metric("總資產（元）", f"{total_assets:,.0f}")
    m2.metric("淨遺產（元）", f"{net_estate:,.0f}")
    m3.metric("課稅基礎（萬）", f"{diag['taxable_base_wan']:,.0f}")
    m4.metric("估算稅額（元）", f"{diag['tax_yuan']:,.0f}")
    m5.metric("建議預留稅源（元）", f"{diag['recommended_liquidity_yuan']:,.0f}")

    st.page_link("pages/3_Result.py", label="➡️ 前往結果頁（含完整報告解鎖）", icon="📄")
