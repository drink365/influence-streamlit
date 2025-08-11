# pages/7_Events_Admin.py
# 事件儀表板（依權限）— tz-naive 修正、缺欄位安全處理

from __future__ import annotations
import streamlit as st
import pandas as pd
from datetime import datetime, timedelta, timezone

st.set_page_config(page_title="事件儀表板（依權限）", page_icon="📈", layout="wide")
st.title("📈 事件儀表板（依權限）")

TZ = timezone(timedelta(hours=8))
NOW = datetime.now(TZ)

def dt_range(days: int):
    end = NOW
    start = (NOW - timedelta(days=days-1)).replace(hour=0, minute=0, second=0, microsecond=0)
    return start, end

def col_or_zero(df: pd.DataFrame, name: str, dtype="int64") -> pd.Series:
    if name in df.columns:
        s = df[name].fillna(0)
        try:
            return s.astype(dtype) if dtype else s
        except Exception:
            return s
    return pd.Series(0, index=df.index, dtype=dtype)

def safe_df(rows) -> pd.DataFrame:
    if rows is None: return pd.DataFrame(columns=["ts", "advisor_id", "advisor_name", "event_type"])
    if isinstance(rows, pd.DataFrame): return rows
    return pd.DataFrame(list(rows))

def human_period(s: datetime, e: datetime) -> str:
    return f"{s.strftime('%Y-%m-%d')} ~ {e.strftime('%Y-%m-%d')}"

try:
    from src.repos.event_repo import EventRepo
except Exception:
    EventRepo = None

def load_events(start_dt: datetime, end_dt: datetime) -> pd.DataFrame:
    if EventRepo is None:
        return pd.DataFrame(columns=["ts","advisor_id","advisor_name","event_type"])
    try:
        if hasattr(EventRepo, "list_range"):
            rows = EventRepo.list_range(start_dt.isoformat(), end_dt.isoformat())
        elif hasattr(EventRepo, "list_since"):
            rows = EventRepo.list_since(start_dt.isoformat())
        elif hasattr(EventRepo, "list_all"):
            rows = EventRepo.list_all()
        else:
            rows = []
    except Exception:
        rows = []

    df = safe_df(rows)
    for col in ["ts","advisor_id","advisor_name","event_type"]:
        if col not in df.columns: df[col] = None

    # tz-naive → UTC-aware → 轉台灣
    try:
        df["ts"] = pd.to_datetime(df["ts"], errors="coerce", utc=True).dt.tz_convert(TZ)
    except Exception:
        df["ts"] = pd.NaT

    mask = df["ts"].between(start_dt, end_dt, inclusive="both")
    df = df[mask.fillna(False)]
    return df

days = st.slider("觀察天數", min_value=7, max_value=120, step=1, value=30)
start_dt, end_dt = dt_range(days)
st.caption(f"期間：{human_period(start_dt, end_dt)}")

role = st.session_state.get("advisor_role", "user")
is_admin = (role == "admin")
st.caption("管理者視角：顯示全站事件" if is_admin else "顧問視角：僅顯示本人事件")

df = load_events(start_dt, end_dt)
if df.empty:
    st.info("這段期間沒有事件紀錄。請稍後再試或調整觀察期間。")
    st.stop()

if not is_admin:
    my_id = st.session_state.get("advisor_id")
    if my_id:
        df = df[df["advisor_id"] == my_id]
    if df.empty:
        st.info("這段期間您尚無事件紀錄。")
        st.stop()

df["event_type"] = df["event_type"].astype(str).str.upper().str.strip()

pivot = (
    df.groupby(["advisor_id", "advisor_name", "event_type"])
      .size()
      .unstack(fill_value=0)
      .reset_index()
)

for col in ["DIAG_DONE", "SHARED", "UNLOCKED", "WON"]:
    if col not in pivot.columns:
        pivot[col] = 0

pivot["Diagnosed"] = (col_or_zero(pivot, "DIAG_DONE")   > 0).astype(int)
pivot["Shared"]    = (col_or_zero(pivot, "SHARED")      > 0).astype(int)
pivot["Unlocked"]  = (col_or_zero(pivot, "UNLOCKED")    > 0).astype(int)
pivot["Won"]       = (col_or_zero(pivot, "WON")         > 0).astype(int)

kpi_cols = ["DIAG_DONE", "SHARED", "UNLOCKED", "WON"]
totals = {k: int(col_or_zero(pivot, k, dtype="int64").sum()) for k in kpi_cols}

c1, c2, c3, c4 = st.columns(4)
c1.metric("完成診斷", f"{totals['DIAG_DONE']:,}")
c2.metric("已分享",   f"{totals['SHARED']:,}")
c3.metric("已解鎖",   f"{totals['UNLOCKED']:,}")
c4.metric("回報成交", f"{totals['WON']:,}")

st.divider()

show_cols = [
    "advisor_name", "advisor_id",
    "DIAG_DONE", "SHARED", "UNLOCKED", "WON",
    "Diagnosed", "Shared", "Unlocked", "Won",
]
existing = [c for c in show_cols if c in pivot.columns]
pivot = pivot[existing].sort_values(by=["WON","UNLOCKED","SHARED","DIAG_DONE"], ascending=False)

st.subheader("顧問事件彙總")
st.dataframe(pivot.reset_index(drop=True), use_container_width=True, hide_index=True)

with st.expander("每日事件趨勢（可選）", expanded=False):
    df["date"] = df["ts"].dt.date
    days_index = pd.date_range(start=start_dt.date(), end=end_dt.date(), freq="D")
    daily = (
        df.groupby(["date", "event_type"])
          .size()
          .unstack(fill_value=0)
          .reindex(days_index.date, fill_value=0)
    )
    for col in ["DIAG_DONE","SHARED","UNLOCKED","WON"]:
        if col not in daily.columns:
            daily[col] = 0
    st.line_chart(daily[["DIAG_DONE","SHARED","UNLOCKED","WON"]])
