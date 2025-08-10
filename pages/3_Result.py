# pages/3_Result.py
import streamlit as st
from src.repos.case_repo import CaseRepo
from src.repos.event_repo import EventRepo
from src.services.reports import generate_docx
from src.services.charts import tax_breakdown_bar, asset_pie
from src.domain.tax_rules import TaxConstants  # 取用當前級距

st.set_page_config(page_title="結果", page_icon="📄", layout="wide")

st.title("📄 診斷結果與報告")
case_id = st.text_input("輸入案件碼 Case ID", placeholder="CASE-20250810-ABCD")

if case_id:
    case = CaseRepo.get(case_id)
    if not case:
        st.error("查無案件，請確認案件碼是否正確。")
        st.stop()

    # 指標
    col = st.columns(3)
    col[0].metric("淨遺產（元）", f"{case['net_estate']:,.0f}")
    col[1].metric("估算稅額（元）", f"{case['tax_estimate']:,.0f}")
    col[2].metric("建議預留稅源（元）", f"{case['liquidity_needed']:,.0f}")

    # 讀 payload 中的課稅基礎（萬）與資產組成
    payload = {}
    try:
        import json
        payload = json.loads(case.get("plan_json") or case.get("payload_json") or "{}")
    except Exception:
        payload = {}

    # 從 payload 取值（兼容之前欄位）
    taxable_base_wan = None
    if isinstance(payload, dict):
        taxable_base_wan = payload.get("taxable_base_wan")
        # 早期版本把參數放在 payload["params"] 內，也接受
        if taxable_base_wan is None and "params" in payload:
            taxable_base_wan = payload["params"].get("taxable_base_wan")

    assets_fin = case.get("assets_financial", 0.0)
    assets_re  = case.get("assets_realestate", 0.0)
    assets_biz = case.get("assets_business", 0.0)

    st.divider()
    st.markdown("### 視覺化總覽")

    c1, c2 = st.columns(2)

    with c1:
        if isinstance(taxable_base_wan, (int, float)):
            st.caption("各級距稅額拆解（依當前稅制）")
            fig1 = tax_breakdown_bar(float(taxable_base_wan), constants=TaxConstants())
            st.pyplot(fig1, use_container_width=True)
        else:
            st.info("找不到課稅基礎（萬）的明細，已略過稅負分布圖。請更新診斷頁後再試。")

    with c2:
        st.caption("資產結構（金融 / 不動產 / 公司股權）")
        fig2 = asset_pie(assets_fin, assets_re, assets_biz)
        st.pyplot(fig2, use_container_width=True)

    st.divider()
    st.markdown("### 檢視報告（簡版）")
    st.info("以下為簡版示意。完整版包含：稅則假設、資產分類明細、策略建議、圖像化傳承圖等。")

    # === 解鎖邏輯 ===
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
