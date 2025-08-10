
import streamlit as st
import pandas as pd
from pathlib import Path

DATA_DIR = Path(__file__).resolve().parent.parent / "data"
CASES_CSV = DATA_DIR / "cases.csv"

st.set_page_config(page_title="診斷結果", page_icon="📊", layout="centered")
st.title("診斷結果（簡版）")

case_id = st.text_input("輸入 CaseID 查詢（若剛完成診斷可直接按下方按鈕）", value=st.session_state.get("last_case_id",""))
if st.button("載入最新個案") and "last_row" in st.session_state:
    row = st.session_state["last_row"]
else:
    row = None
    if case_id and Path(CASES_CSV).exists():
        df = pd.read_csv(CASES_CSV)
        m = df[df["case_id"]==case_id]
        if not m.empty:
            row = m.iloc[-1].to_dict()

if not row:
    st.info("請先在左側輸入 CaseID，或回到『傳承規劃｜快速診斷』建立個案。")
    st.page_link("pages/1_🧭_Diagnostic.py", label="前往診斷", icon="🧭")
    st.stop()

st.markdown(f"**個案編號：** `{row['case_id']}`  
**申請人：** {row.get('name','（未填）')}")

st.divider()
st.subheader("一、風險重點")
st.write(f"- 資產總額（估）：**{int(row['total_assets']):,} 萬**")
st.write(f"- 流動性需求（估）：**{int(row['liquidity_need_low']):,}–{int(row['liquidity_need_high']):,} 萬**")
st.write(f"- 現有保單保額：**{int(row['insurance_coverage']):,} 萬**")
st.write(f"- 可能的保障缺口範圍：**{int(row['coverage_gap_low']):,}–{int(row['coverage_gap_high']):,} 萬**")

st.caption("說明：以上為示意試算，實際仍需依照家庭目標、法規與細部資產結構調整。")

st.divider()
st.subheader("二、可行方向（草案）")
bullets = [
    "以保單建立緊急流動性池，避免交棒時資金壓力。",
    "評估是否需要信託來管理特殊照顧對象或特定資產的分配節奏。",
    "針對股權與不動產，規劃適當的傳承順序與治理安排。",
    "視需要規劃遺囑，確保意願清楚、減少爭議。",
]
for b in bullets:
    st.write(f"- {b}")

st.divider()
st.subheader("三、下一步")
st.write("建議預約 30 分鐘線上會談，根據您的實際資料生成完整方案。")
st.page_link("pages/3_📅_Book.py", label="立即預約", icon="📅")
st.page_link("pages/5_💳_Plans.py", label="顧問方案與授權", icon="💳")
