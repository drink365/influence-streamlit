import streamlit as st
from datetime import datetime
import pytz, uuid
from src.repos.case_repo import CaseRepo
from src.repos.event_repo import EventRepo

st.set_page_config(page_title="診斷", page_icon="🧮", layout="wide")

st.title("🧮 傳承風險診斷")

with st.form("diag"):
    col1, col2 = st.columns(2)
    with col1:
        client_alias = st.text_input("客戶稱呼", placeholder="例如：李先生")
        assets_financial = st.number_input("金融資產", min_value=0.0, step=100000.0, format="%.0f")
        assets_realestate = st.number_input("不動產市值合計", min_value=0.0, step=100000.0, format="%.0f")
        assets_business = st.number_input("公司股權估值", min_value=0.0, step=100000.0, format="%.0f")
        liabilities = st.number_input("負債總額", min_value=0.0, step=100000.0, format="%.0f")
    with col2:
        st.markdown("#### 隱私與告知")
        agree = st.checkbox("我已閱讀並同意隱私權政策與資料使用說明。")
        st.caption("＊此診斷僅供參考，完整規劃以專業顧問審核為準。")
    submitted = st.form_submit_button("🚀 立即試算", type="primary", disabled=not agree)

if submitted:
    total_assets = assets_financial + assets_realestate + assets_business
    net_estate = max(total_assets - liabilities, 0)

    # TODO: 將稅則抽象化；此處為簡化示意
    def tax_estimate(v):
        brackets = [(0,0.1),(50_000_000,0.15),(100_000_000,0.2),(200_000_000,0.3)]
        tax=0; prev=0; rate=brackets[0][1]
        for th, r in brackets[1:]:
            if v>th:
                tax += (th-prev)*rate; prev=th; rate=r
            else:
                tax += (v-prev)*rate; return max(tax,0)
        tax += (v-prev)*rate; return max(tax,0)

    tax = tax_estimate(net_estate)
    liquidity_needed = round(tax*1.1)

    # 產生 Case ID（台北時區）
    tz = pytz.timezone("Asia/Taipei")
    date_str = datetime.now(tz).strftime("%Y%m%d")
    short = str(uuid.uuid4())[:4].upper()
    case_id = f"CASE-{date_str}-{short}"

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
        "tax_estimate": tax,
        "liquidity_needed": liquidity_needed,
        "status": "Prospect",
        "payload": {"assets_total": total_assets, "params": {"buffer": 1.1}},
    })
    EventRepo.log(case_id, "DIAG_DONE", {"net_estate": net_estate, "tax": tax})

    st.success(f"已完成試算，案件碼：**{case_id}**")
    m1,m2,m3,m4 = st.columns(4)
    m1.metric("總資產", f"{total_assets:,.0f}")
    m2.metric("淨遺產", f"{net_estate:,.0f}")
    m3.metric("估算稅額", f"{tax:,.0f}")
    m4.metric("建議預留稅源", f"{liquidity_needed:,.0f}")

    st.page_link("pages/3_Result.py", label="➡️ 前往結果頁（含完整報告解鎖）", icon="📄")
