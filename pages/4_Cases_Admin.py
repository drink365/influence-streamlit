import streamlit as st
from datetime import datetime, timezone
from zoneinfo import ZoneInfo
from pathlib import Path

from src.ui.footer import footer
from src.config import ADMIN_KEY, DATA_DIR
from src.repos.cases import CaseRepo

st.title("案件總表（管理）")
repo = CaseRepo()

# 狀態初始化
if "admin_ok" not in st.session_state:
    st.session_state.admin_ok = False

# 解析並轉成台北時間的工具（同時相容舊資料的 UTC ISO）
TPE = ZoneInfo("Asia/Taipei")
def to_taipei_human(ts_str: str) -> str:
    """嘗試把多種格式的時間字串轉為台北時間易讀字串"""
    if not ts_str:
        return ""
    # 已經是人類可讀（例如：2025-08-10 21:15:01 TST）
    for fmt in ("%Y-%m-%d %H:%M:%S %Z", "%Y-%m-%d %H:%M:%S"):
        try:
            dt = datetime.strptime(ts_str, fmt)
            # 無時區標記時視為台北本地時間
            if dt.tzinfo is None:
                dt = dt.replace(tzinfo=TPE)
            return dt.astimezone(TPE).strftime("%Y-%m-%d %H:%M:%S %Z")
        except Exception:
            pass
    # 常見 ISO 格式（UTC）
    try:
        s = ts_str.replace("Z", "+00:00")
        dt = datetime.fromisoformat(s)
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=timezone.utc)
        return dt.astimezone(TPE).strftime("%Y-%m-%d %H:%M:%S %Z")
    except Exception:
        return ts_str  # 兜底：原樣顯示

# 驗證（放在 on_change，不呼叫 st.rerun）
def _verify_sidebar():
    st.session_state.admin_ok = (st.session_state.get("admin_key_sidebar", "") == ADMIN_KEY)
    if st.session_state.admin_ok:
        st.toast("已通過驗證，正在載入資料…", icon="✅")
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
    # 下載 bookings.csv（即使沒有個案，也允許抓預約名單）
    from src.config import DATA_DIR as _DD
    bookings_csv = Path(_DD) / "bookings.csv"
    if bookings_csv.exists():
        with bookings_csv.open("rb") as f:
            st.download_button("下載 bookings.csv", data=f.read(), file_name="bookings.csv", mime="text/csv", use_container_width=True)
    footer(); st.stop()

# 轉換展示用時間
rows_view = []
for r in rows:
    r_copy = dict(r)
    r_copy["ts_local"] = to_taipei_human(r.get("ts", ""))
    rows_view.append(r_copy)

st.subheader("案件列表")
kw = st.text_input("姓名 / Email 關鍵字", "")
recent_days = st.number_input("僅看最近 N 天（0 表示不限制）", min_value=0, max_value=3650, value=0, step=1)

view = rows_view
if kw:
    view = [r for r in view if kw.lower() in (r.get("name","") + r.get("email","")).lower()]

# 依原始 ts（盡量相容 ISO）做篩選，但顯示用 ts_local
if recent_days:
    now_tpe = datetime.now(TPE)
    def within_days(ts_raw):
        try:
            s = (ts_raw or "").replace("Z", "+00:00")
            dt = datetime.fromisoformat(s)
            if dt.tzinfo is None:
                # 舊資料若無時區，視為 UTC
                dt = dt.replace(tzinfo=timezone.utc)
            return (now_tpe - dt.astimezone(TPE)).days <= recent_days
        except Exception:
            # 若不可解析，保守地保留顯示
            return True
    view = [r for r in view if within_days(r.get("ts",""))]

# 顯示資料（包含台北時間欄位）
if view:
    # 調整欄位順序：台北時間置前
    cols_order = ["ts_local","case_id","name","email","mobile","marital","children","equity","real_estate","financial","insurance_cov","total_assets"]
    # 補不存在欄位
    for r in view:
        for c in cols_order:
            r.setdefault(c, r.get(c, ""))
    st.dataframe(view, use_container_width=True, height=420, column_config={"ts_local": "建立時間（台北）"})
else:
    st.info("沒有符合篩選條件的資料。")

# 前往結果頁
case_ids = [r.get("case_id") for r in view if r.get("case_id")]
if case_ids:
    selected = st.selectbox("選擇 CaseID 前往檢視結果", case_ids)
    if st.button("前往結果頁"):
        st.session_state["last_case_id"] = selected
        st.switch_page("pages/3_Result.py")

# 下載 cases.csv
cases_csv = Path(DATA_DIR) / "cases.csv"
if cases_csv.exists():
    with cases_csv.open("rb") as f:
        st.download_button("下載 cases.csv", data=f.read(), file_name="cases.csv", mime="text/csv", use_container_width=True)

# 下載 bookings.csv
bookings_csv = Path(DATA_DIR) / "bookings.csv"
if bookings_csv.exists():
    with bookings_csv.open("rb") as f:
        st.download_button("下載 bookings.csv", data=f.read(), file_name="bookings.csv", mime="text/csv", use_container_width=True)

footer()
