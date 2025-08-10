
import streamlit as st
import uuid, datetime, pandas as pd
from pathlib import Path

DATA_DIR = Path(__file__).resolve().parent.parent / "data"
DATA_DIR.mkdir(parents=True, exist_ok=True)
CASES_CSV = DATA_DIR / "cases.csv"

st.set_page_config(page_title="傳承規劃｜診斷", page_icon="🧭", layout="centered")

st.title("傳承規劃｜快速診斷")
st.write("填寫 60 秒，取得初步風險指標與行動建議。")

with st.form("diagnostic_form"):
    st.subheader("家庭結構")
    col1, col2, col3 = st.columns(3)
    marital = col1.selectbox("婚姻狀態", ["未婚","已婚","離異","喪偶"])
    children = col2.number_input("子女數", min_value=0, max_value=10, step=1, value=2)
    special_needs = col3.selectbox("是否有特殊照顧對象", ["否","是"])

    st.subheader("資產概況（估算即可）")
    col4, col5 = st.columns(2)
    equity = col4.number_input("公司股權（估值，萬元）", min_value=0, step=100, value=5000)
    real_estate = col5.number_input("不動產（估值，萬元）", min_value=0, step=100, value=8000)

    col6, col7 = st.columns(2)
    financial = col6.number_input("金融資產（估值，萬元）", min_value=0, step=100, value=3000)
    insurance_coverage = col7.number_input("既有保單保額（萬元）", min_value=0, step=100, value=2000)

    st.subheader("您的重點關注（多選）")
    focus = st.pills("選擇重點", ["稅務負擔","現金流穩定","交棒安排","家族和諧","跨境安排"], selection_mode="multi")

    st.subheader("聯絡方式")
    c1, c2 = st.columns(2)
    name = c1.text_input("姓名")
    mobile = c2.text_input("手機")
    email = st.text_input("Email")

    submitted = st.form_submit_button("產生診斷結果與 CaseID")
    if submitted:
        case_id = "YC-" + uuid.uuid4().hex[:8].upper()
        total_assets = equity + real_estate + financial

        # 簡化的流動性缺口估算（示意）
        liquidity_need_low = round(total_assets * 0.10, 0)
        liquidity_need_high = round(total_assets * 0.20, 0)
        coverage_gap_low = max(0, liquidity_need_low - insurance_coverage)
        coverage_gap_high = max(0, liquidity_need_high - insurance_coverage)

        row = dict(
            timestamp=datetime.datetime.utcnow().isoformat(),
            case_id=case_id, name=name, mobile=mobile, email=email,
            marital=marital, children=int(children), special_needs=special_needs,
            equity=float(equity), real_estate=float(real_estate), financial=float(financial),
            insurance_coverage=float(insurance_coverage), focus=",".join(focus),
            total_assets=float(total_assets),
            liquidity_need_low=float(liquidity_need_low),
            liquidity_need_high=float(liquidity_need_high),
            coverage_gap_low=float(coverage_gap_low),
            coverage_gap_high=float(coverage_gap_high),
        )

        # 儲存到 CSV
        df = pd.DataFrame([row])
        if CASES_CSV.exists():
            old = pd.read_csv(CASES_CSV)
            df = pd.concat([old, df], ignore_index=True)
        df.to_csv(CASES_CSV, index=False)

        st.success(f"已建立個案：{case_id}")
        st.session_state["last_case_id"] = case_id
        st.session_state["last_row"] = row
        st.page_link("pages/2_📊_Result.py", label="查看診斷結果", icon="➡️")
