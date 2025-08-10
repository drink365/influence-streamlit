import streamlit as st
from datetime import datetime, timezone
from src.ui.footer import footer
from src.config import ADMIN_KEY
from src.repos.cases import CaseRepo

st.title("案件總表（管理）")
repo = CaseRepo()

# 驗證（即時 on_change）
if "admin_ok" not in st.session_state:
    st.session_state.admin_ok = False

def _verify_sidebar():
    st.session_state.admin_ok = (st.session_state.get("admin_key_sidebar", "") == ADMIN_KEY)
    if st.session_state.admin_ok:
        st.toast("已通過驗證，正在載入資料…", icon="✅"); st.rerun()
    else:
        st.toast("密鑰錯誤", icon="❌")

with st.sidebar:
    st.subheader("管理密鑰")
    st.text_input("請輸入管理密鑰", type="password", key="admin_key_sidebar", on_change=_verify_sidebar)

if not st.session_state.admin_ok:
    st.warning("此頁需管理密鑰。")
    footer(); st.stop()

rows = repo.get_all()
if not rows:
    st.info("目前尚無個案資料。請先到『診斷』頁建立個案。")
    footer(); st.stop()

# 篩選
kw = st.text_input("姓名 / Email 關鍵字", "")
recent_days = st.number_input("僅看最近 N 天（0 表示不限制）", min_value=0, max_value=3650, value=0, step=1)

view = rows
if kw:
    view = [r for r in view if kw.lower() in (r.get("name","") + r.get("email","")) .lower()]
if recent_days:
    cutoff = datetime.now(timezone.utc)
    def within_days(ts):
        try:
            from datetime import datetime as dt
            return (cutoff - dt.fromisoformat((ts or "").replace("Z",""))).days <= recent_days
        except Exception:
            return True
    view = [r for r in view if within_days(r.get("ts",""))]

st.dataframe(view, use_container_width=True, height=420)
case_ids = [r.get("case_id") for r in view if r.get("case_id")]
if case_ids:
    selected = st.selectbox("選擇 CaseID 前往檢視結果", case_ids)
    if st.button("前往結果頁"):
        st.session_state["last_case_id"] = selected
        st.switch_page("pages/3_📊_Result.py")

# 下載 CSV
from pathlib import Path
from src.config import DATA_DIR
cases_csv = Path(DATA_DIR) / "cases.csv"
if cases_csv.exists():
    with cases_csv.open("rb") as f:
        st.download_button("下載 cases.csv", data=f.read(), file_name="cases.csv", mime="text/csv", use_container_width=True)

footer()
