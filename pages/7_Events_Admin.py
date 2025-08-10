import streamlit as st
import pandas as pd
from datetime import datetime, timedelta
from src.db import get_conn

st.set_page_config(page_title="事件儀表板", page_icon="📈", layout="wide")

st.title("📈 事件儀表板（漏斗＆轉換＋KPI 擴充）")

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

# 基本漏斗
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
    "策略模擬次數": int((df["event"]=="STRATEGY_SIMULATED").sum()),
}

base = max(summary["診斷數"], 1)
conv_unlock = summary["解鎖數"]/base
conv_book   = summary["預約數"]/base
conv_won    = summary["成交數"]/base

m1, m2, m3, m4, m5 = st.columns(5)
m1.metric("診斷數", summary["診斷數"])
m2.metric("解鎖率", f"{conv_unlock*100:.1f}%")
m3.metric("預約率", f"{conv_book*100:.1f}%")
m4.metric("成交率", f"{conv_won*100:.1f}%")
m5.metric("策略模擬次數", summary["策略模擬次數"])

st.divider()

# 解鎖方式占比
unlock_df = df[df["event"] == "REPORT_UNLOCKED"].copy()
method_ratio = "—"
if not unlock_df.empty:
    # 嘗試解析 meta 的 by 欄位
    import json
    def get_by(s):
        try:
            o = json.loads(s or "{}")
            return o.get("by", "unknown")
        except Exception:
            return "unknown"
    unlock_df["by"] = unlock_df["meta"].map(get_by)
    by_counts = unlock_df["by"].value_counts()
    st.markdown("### 解鎖方式占比")
    st.bar_chart(by_counts)
else:
    st.info("期間內尚無解鎖事件。")

st.markdown("### 事件明細（期間內）")
st.dataframe(df.sort_values("created_at", ascending=False), use_container_width=True)

st.markdown("### 個案漏斗狀態（行為矩陣）")
st.dataframe(pivot.reset_index(), use_container_width=True)
