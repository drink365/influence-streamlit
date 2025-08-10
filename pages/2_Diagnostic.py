import streamlit as st
import uuid
from src.ui.theme import inject_css
inject_css()

from src.ui.footer import footer
from src.repos.cases import CaseRepo
from src.utils import utc_now_iso

st.title("傳承規劃｜快速診斷（MVP）")
st.write("填寫 60 秒，取得初步風險指標與行動建議。")

repo = CaseRepo()

with st.form("diag"):
    st.subheader("家庭結構")
    c1, c2, c3 = st.columns(3)
    marital = c1.selectbox("婚姻狀態", ["已婚", "未婚", "離異", "喪偶"])
    children = c2.number_input("子女數", min_value=0, max_value=10, step=1, value=2)
    special = c3.selectbox("是否有特殊照顧對象", ["否", "是"])

    st.subheader("資產概況（估算即可，單位：萬元）")
    c4, c5 = st.columns(2)
    equity = c4.number_input("公司股權估值", min_value=0, step=100, value=5000)
    real_estate = c5.number_input("不動產估值", min_value=0, step=100, value=8000)
    c6, c7 = st.columns(2)
    financial = c6.number_input("金融資產估值", min_value=0, step=100, value=3000)
    insurance_cov = c7.number_input("既有保單保額", min_value=0, step=100, value=2000)

    st.subheader("您的重點關注（可多選）")
    focus = st.multiselect(
        "選擇重點",
        ["稅務負擔", "現金流穩定", "交棒安排", "家族和諧", "跨境安排"],
        default=["現金流穩定", "交棒安排"],
    )

    st.subheader("聯絡方式")
    c8, c9 = st.columns(2)
    name = c8.text_input("姓名")
    mobile = c9.text_input("手機")
    email = st.text_input("Email")

    submitted = st.form_submit_button("產生診斷結果與 CaseID")

if submitted:
    case_id = "YC-" + uuid.uuid4().hex[:6].upper()
    total_assets = equity + real_estate + financial
    liq_low = round(total_assets * 0.10)
    liq_high = round(total_assets * 0.20)
    gap_low = max(0, liq_low - insurance_cov)
    gap_high = max(0, liq_high - insurance_cov)

    repo.add({
        "ts": utc_now_iso(),
        "case_id": case_id,
        "name": name, "mobile": mobile, "email": email,
        "marital": marital, "children": int(children), "special": special,
        "equity": int(equity), "real_estate": int(real_estate), "financial": int(financial),
        "insurance_cov": int(insurance_cov),
        "focus": "|".join(focus),
        "total_assets": int(total_assets),
        "liq_low": int(liq_low), "liq_high": int(liq_high),
        "gap_low": int(gap_low), "gap_high": int(gap_high),
    })

    st.session_state["last_case_id"] = case_id
    st.success(f"已建立個案：{case_id}")
    st.switch_page("pages/3_Result.py")

footer()
