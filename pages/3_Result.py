import streamlit as st, json
from datetime import date

from src.repos.case_repo import CaseRepo
from src.repos.event_repo import EventRepo
from src.services.reports import generate_docx
from src.services.charts import tax_breakdown_bar, asset_pie, savings_compare_bar, simple_sankey
from src.domain.tax_loader import load_tax_constants
from src.domain.tax_rules import EstateTaxCalculator

st.set_page_config(page_title="結果", page_icon="📄", layout="wide")

st.title("📄 診斷結果與報告")
case_id = st.text_input("輸入案件碼 Case ID", placeholder="CASE-20250810-ABCD")

if case_id:
    case = CaseRepo.get(case_id)
    if not case:
        st.error("查無案件，請確認案件碼是否正確。")
        st.stop()

    col = st.columns(3)
    col[0].metric("淨遺產（元）", f"{case['net_estate']:,.0f}")
    col[1].metric("估算稅額（元）", f"{case['tax_estimate']:,.0f}")
    col[2].metric("建議預留稅源（元）", f"{case['liquidity_needed']:,.0f}")

    payload = {}
    try:
        payload = json.loads(case.get("plan_json") or case.get("payload_json") or "{}")
    except Exception:
        payload = {}

    taxable_base_wan = None
    if isinstance(payload, dict):
        taxable_base_wan = payload.get("taxable_base_wan")
        if taxable_base_wan is None and "params" in payload:
            taxable_base_wan = payload["params"].get("taxable_base_wan")

    assets_fin = case.get("assets_financial", 0.0)
    assets_re  = case.get("assets_realestate", 0.0)
    assets_biz = case.get("assets_business", 0.0)
    total_assets = (payload.get("assets_total") if isinstance(payload, dict) else None) or (assets_fin + assets_re + assets_biz)

    st.divider()
    st.markdown("### 視覺化總覽")

    c1, c2 = st.columns(2)

    with c1:
        # 若沒有 taxable_base_wan，回推
        if taxable_base_wan is None:
            constants = load_tax_constants(on_date=date.today())
            calc = EstateTaxCalculator(constants)
            params = (payload.get("params") or {})
            has_spouse = bool(params.get("has_spouse", False))
            adult_children = int(params.get("adult_children", 0))
            parents = int(params.get("parents", 0))
            disabled_people = int(params.get("disabled_people", 0))
            other_dependents = int(params.get("other_dependents", 0))
            net_wan = float(case["net_estate"]) / constants.UNIT_FACTOR
            ded_wan = calc.compute_total_deductions_wan(has_spouse, adult_children, parents, disabled_people, other_dependents)
            taxable_base_wan = calc.compute_taxable_base_wan(net_wan, ded_wan)

        st.caption("各級距稅額拆解（依當前稅制）")
        fig1 = tax_breakdown_bar(float(taxable_base_wan), constants=load_tax_constants(on_date=date.today()))
        st.pyplot(fig1, use_container_width=True)

    with c2:
        st.caption("資產結構（金融 / 不動產 / 公司股權）")
        fig2 = asset_pie(assets_fin, assets_re, assets_biz)
        st.pyplot(fig2, use_container_width=True)

    # === 策略模擬區（不宣稱減稅，以資金缺口對比表述） ===
    st.divider()
    st.markdown("### 策略模擬（資金缺口對比）")
    reserve_default = float(case.get("liquidity_needed", 0.0))
    reserve = st.number_input("方案預留稅源（元）", min_value=0.0, step=100000.0, format="%.0f", value=reserve_default)

    cc1, cc2 = st.columns(2)
    with cc1:
        fig3 = savings_compare_bar(float(case['tax_estimate']), reserve)
        st.pyplot(fig3, use_container_width=True)
    with cc2:
        fig4 = simple_sankey(total_assets, float(case['tax_estimate']), reserve)
        st.pyplot(fig4, use_container_width=True)

    if st.button("記錄此次策略模擬"):
        EventRepo.log(case_id, "STRATEGY_SIMULATED", {"reserve": reserve, "tax": float(case['tax_estimate'])})
        st.toast("已記錄策略模擬", icon="✅")

    st.divider()
    st.markdown("### 檢視報告（簡版）")
    st.info("以下為簡版示意。完整版包含：稅則假設、資產分類明細、策略建議、圖像化傳承圖等。")

    st.markdown("### 解鎖完整版報告")
    tabs = st.tabs(["A. 管理碼解鎖","B. 成交回報解鎖（推薦）"])

    with tabs[0]:
        admin_key = st.text_input("管理碼", type="password")
        if st.button("用管理碼解鎖"):
            if admin_key and admin_key == st.secrets.get("ADMIN_KEY", ""):
                EventRepo.log(case_id, "REPORT_UNLOCKED", {"by":"admin_key"})
                fname = generate_docx(case, full=True)
                st.success("已解鎖完整版報告！")
                with open(f"data/reports/{fname}", "rb") as f:
                    st.download_button("⬇️ 下載 DOCX（完整版）", data=f, file_name=fname)
            else:
                st.error("管理碼不正確。")

    with tabs[1]:
        st.caption("完成成交回報即可解鎖完整版報告，並回饋顧問點數（可設定）。")
        with st.form("won_form"):
            product = st.selectbox("產品別", ["壽險","年金","醫療","投資型","其他"])
            premium = st.number_input("年繳保費（元）", min_value=0.0, step=10000.0, format="%.0f")
            remark = st.text_area("備註（可填入公司/商品名稱、要保關係等）")
            submitted = st.form_submit_button("回報成交並解鎖")
        if submitted:
            CaseRepo.update_status(case_id, "Won")
            EventRepo.log(case_id, "WON_REPORTED", {"product": product, "premium": premium, "remark": remark})
            fname = generate_docx(case, full=True)
            st.success("謝謝回報！已解鎖完整版報告。")
            with open(f"data/reports/{fname}", "rb") as f:
                st.download_button("⬇️ 下載 DOCX（完整版）", data=f, file_name=fname)
