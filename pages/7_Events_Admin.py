import streamlit as st
import pandas as pd
from datetime import datetime, timedelta
from src.db import get_conn
from src.services.auth import is_logged_in, current_role

st.set_page_config(page_title="事件儀表板", page_icon="📈", layout="wide")

st.title("📈 事件儀表板（依權限）")

conn = get_conn()

df = pd.read_sql_query("SELECT * FROM events", conn)
if df.empty:
    st.info("尚無事件紀錄。去跑一筆診斷試試吧！")
    st.stop()

try:
    df["created_at"] = pd.to_datetime(df["created_at"])  # ISO
except Exception:
    pass

colA, colB = st.columns(2)
with colA:
    days = st.slider("觀察天數", 1, 90, 30)
with colB:
    start = datetime.utcnow() - timedelta(days=days)
    st.caption(f"期間：{start:%Y-%m-%d} ~ {datetime.utcnow():%Y-%m-%d}")

mask = df["created_at"] >= pd.Timestamp(start)
df = df.loc[mask].copy()

# 權限：非 admin 僅看自己案件的事件
if is_logged_in() and current_role() != "admin":
    # 抓出當前顧問的 case_id 清單
    cases = pd.read_sql_query("SELECT id, advisor_id FROM cases", conn)
    my_cases = cases.loc[cases["advisor_id"] == st.session_state.get("advisor_id"), "id"].tolist()
    df = df[df["case_id"].isin(my_cases)]
    st.caption(f"已套用過濾：只看顧問 {st.session_state.get('advisor_name')} 的案件事件（{len(my_cases)} 筆案件）")
else:
    st.caption("管理者視角：顯示全站事件")

if df.empty:
    st.info("範圍內沒有可顯示的事件。")
    st.stop()

# 漏斗統計
pivot = df.pivot_table(index="case_id", columns="event", values="id", aggfunc="count", fill_value=0)
pivot["Diagnosed"] = (pivot.get("DIAG_DONE", 0) > 0).astype(int)
pivot["Unlocked"] = (pivot.get("REPORT_UNLOCKED", 0) > 0).astype(int)
pivot["Booked"]   = (pivot.get("BOOKING_CREATED", 0) > 0).astype(int)
pivot["Won"]      = (pivot.get("WON_REPORTED", 0) > 0).astype(int)

summary = {
    "診斷數": int(pivot["Diagnosed"].sum()),
    "解鎖數": int(pivot["Unlocked"].sum()),
    "預約數": int(pivot["Booked"].sum()),
    "成交數": int(pivot["Won"].sum()),
}

base = max(summary["診斷數"], 1)
conv_unlock = summary["解鎖數"]/base
conv_book   = summary["預約數"]/base
conv_won    = summary["成交數"]/base

m1, m2, m3, m4 = st.columns(4)
m1.metric("診斷數", summary["診斷數"])
m2.metric("解鎖率", f"{conv_unlock*100:.1f}%")
m3.metric("預約率", f"{conv_book*100:.1f}%")
m4.metric("成交率", f"{conv_won*100:.1f}%")

st.divider()

st.markdown("### 事件明細（期間內）")
st.dataframe(df.sort_values("created_at", ascending=False), use_container_width=True)

st.markdown("### 個案漏斗狀態（行為矩陣）")
st.dataframe(pivot.reset_index(), use_container_width=True)
