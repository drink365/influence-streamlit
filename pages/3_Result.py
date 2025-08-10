import streamlit as st, json
from datetime import date

from src.repos.case_repo import CaseRepo
from src.repos.event_repo import EventRepo
from src.services.reports import generate_docx
from src.services.reports_pdf import build_pdf_report
from src.services.charts import tax_breakdown_bar, asset_pie, savings_compare_bar, simple_sankey
from src.domain.tax_loader import load_tax_constants
from src.domain.tax_rules import EstateTaxCalculator
from src.services.billing import try_unlock_full_report, reward_won, balance, REPORT_FULL_COST

st.set_page_config(page_title="結果", page_icon="📄", layout="wide")

st.title("📄 診斷結果與報告（含點數解鎖）")
case_id = st.text_input("輸入案件碼 Case ID", placeholder="CASE-20250810-ABCD")

advisor_id = st.session_state.get("advisor_id", "guest")
advisor_name = st.session_state.get("advisor_name", "未登入")

if case_id:
    case = CaseRepo.get(case_id)
    if not case:
        st.error("查無案件，請確認案件碼是否正確。")
        st.stop()

    col0 = st.columns(3)
    col0[0].metric("我的點數", balance(advisor_id))
    col0[1].metric("顧問", advisor_name)

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

    # === 策略模擬區 ===
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
    st.markdown("### 檢視報告（簡/全）")
    st.info(f"完整版 PDF/DOCX 需解鎖：每次 {REPORT_FULL_COST} 點。管理碼仍可免費解鎖（內部使用）。")

    tabs = st.tabs(["A. 使用點數解鎖（顧問）","B. 管理碼解鎖（內部）","C. 成交回報解鎖（回饋點）"])

    def _download_full_reports(current_case):
        path = build_pdf_report(current_case)
        label = "⬇️ 下載 PDF（完整版）" if path.suffix.lower() == ".pdf" else "⬇️ 下載 HTML（完整版）"
        with open(path, "rb") as f:
            st.download_button(label, data=f, file_name=path.name)
        fname = generate_docx(current_case, full=True)
        with open(f"data/reports/{fname}", "rb") as f:
            st.download_button("⬇️ 下載 DOCX（完整版）", data=f, file_name=fname)

    with tabs[0]:
        if st.button(f"使用 {REPORT_FULL_COST} 點解鎖並下載", type="primary"):
            ok, msg = try_unlock_full_report(advisor_id, case_id)
            if ok:
                EventRepo.log(case_id, "REPORT_UNLOCKED", {"by":"credits"})
                st.success(msg)
                _download_full_reports(case)
            else:
                st.error(msg)
                st.caption("前往顧問 Dashboard → 測試儲值加點。")
                st.page_link("pages/8_Advisor_Dashboard.py", label="➡️ 顧問 Dashboard", icon="🧭")

    with tabs[1]:
        admin_key = st.text_input("管理碼", type="password")
        if st.button("用管理碼解鎖"):
            if admin_key and admin_key == st.secrets.get("ADMIN_KEY", ""):
                EventRepo.log(case_id, "REPORT_UNLOCKED", {"by":"admin_key"})
                st.success("已解鎖完整版報告！")
                _download_full_reports(case)
            else:
                st.error("管理碼不正確。")

    with tabs[2]:
        st.caption("完成成交回報即可解鎖完整版報告，並回饋點數（預設 +5）。")
        with st.form("won_form"):
            product = st.selectbox("產品別", ["壽險","年金","醫療","投資型","其他"])
            premium = st.number_input("年繳保費（元）", min_value=0.0, step=10000.0, format="%.0f")
            remark = st.text_area("備註（可填入公司/商品名稱、要保關係等）")
            submitted = st.form_submit_button("回報成交並解鎖")
        if submitted:
            CaseRepo.update_status(case_id, "Won")
            EventRepo.log(case_id, "WON_REPORTED", {"product": product, "premium": premium, "remark": remark})
            reward_won(advisor_id, case_id, premium)
            st.success("謝謝回報！已回饋點數並解鎖完整版報告。")
            _download_full_reports(case)
