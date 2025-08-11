# pages/7_Events_Admin.py
# 事件儀表板（依權限）
# - 安全處理缺欄位：不再使用 pivot.get(..., 0)，改以 col_or_zero
# - 支援多種資料來源 API（list_range / list_since / list_all）
# - admin 看全站；一般顧問只看自己
# - 若無資料，友善顯示而不報錯

from __future__ import annotations
import streamlit as st
import pandas as pd
from datetime import datetime, timedelta, timezone

st.set_page_config(page_title="事件儀表板（依權限）", page_icon="📈", layout="wide")
st.title("📈 事件儀表板（依權限）")

# ---------------- Utilities ----------------
TZ = timezone(timedelta(hours=8))  # 顯示台灣時間；若要 UTC 可改掉
NOW = datetime.now(TZ)

def dt_range(days: int):
    end = NOW
    start = (NOW - timedelta(days=days-1)).replace(hour=0, minute=0, second=0, microsecond=0)
    return start, end

def col_or_zero(df: pd.DataFrame, name: str, dtype="int64") -> pd.Series:
    """若欄位存在回傳該欄（NaN→0）；否則回傳 index 對齊的 0 Series。"""
    if name in df.columns:
        s = df[name].fillna(0)
        if dtype:
            try:
                return s.astype(dtype)
            except Exception:
                return s
        return s
    return pd.Series(0, index=df.index, dtype=dtype)

def safe_df(rows) -> pd.DataFrame:
    if rows is None:
        return pd.DataFrame(columns=["ts", "advisor_id", "advisor_name", "event_type"])
    if isinstance(rows, pd.DataFrame):
        return rows
    return pd.DataFrame(list(rows))

def human_period(s: datetime, e: datetime) -> str:
    return f"{s.strftime('%Y-%m-%d')} ~ {e.strftime('%Y-%m-%d')}"

# ---------------- Data Source ----------------
# 嘗試多種 Repo 實作，失敗就回空表
try:
    from src.repos.event_repo import EventRepo
except Exception:
    EventRepo = None

def load_events(start_dt: datetime, end_dt: datetime) -> pd.DataFrame:
    if EventRepo is None:
        return pd.DataFrame(columns=["ts","advisor_id","advisor_name","event_type"])
    try:
        # 優先區間查詢
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
    # 正規化欄位
    for col in ["ts","advisor_id","advisor_name","event_type"]:
        if col not in df.columns:
            df[col] = None
    # 轉為 datetime 方便篩選
    try:
        df["ts"] = pd.to_datetime(df["ts"])
    except Exception:
        df["ts"] = pd.NaT
    # 區間過濾
    mask = (df["ts"] >= start_dt) & (df["ts"] <= end_dt)
    df = df[mask.fillna(False)]
    return df

# ---------------- Controls ----------------
days = st.slider("觀察天數", min_value=7, max_value=120, step=1, value=30)
start_dt, end_dt = dt_range(days)
st.caption(f"期間：{human_period(start_dt, end_dt)}")

# 權限：admin 看全站
role = st.session_state.get("advisor_role", "user")
is_admin = (role == "admin")
if is_admin:
    st.caption("管理者視角：顯示全站事件")
else:
    st.caption("顧問視角：僅顯示本人事件")

# ---------------- Load & Filter ----------------
df = load_events(start_dt, end_dt)

if df.empty:
    st.info("這段期間沒有事件紀錄。請稍後再試或縮短/放寬觀察期間。")
    st.stop()

# 顧問視角：只看自己
if not is_admin:
    my_id = st.session_state.get("advisor_id")
    if my_id:
        df = df[df["advisor_id"] == my_id]
    if df.empty:
        st.info("這段期間您尚無事件紀錄。")
        st.stop()

# ---------------- Aggregation ----------------
# 統一事件名稱（你專案常見：DIAG_DONE / SHARED / UNLOCKED / WON）
df["event_type"] = df["event_type"].astype(str).str.upper().str.strip()

# 以顧問彙總各事件的次數
pivot = (
    df.groupby(["advisor_id", "advisor_name", "event_type"])
      .size()
      .unstack(fill_value=0)
      .reset_index()
)

# 保障欄位存在（即使沒發生也有 0）
for col in ["DIAG_DONE", "SHARED", "UNLOCKED", "WON"]:
    if col not in pivot.columns:
        pivot[col] = 0

# 派生欄位（是否至少有一次）— 使用 col_or_zero 避免 .get(0) 問題
pivot["Diagnosed"] = (col_or_zero(pivot, "DIAG_DONE")   > 0).astype(int)
pivot["Shared"]    = (col_or_zero(pivot, "SHARED")      > 0).astype(int)
pivot["Unlocked"]  = (col_or_zero(pivot, "UNLOCKED")    > 0).astype(int)
pivot["Won"]       = (col_or_zero(pivot, "WON")         > 0).astype(int)

# 總覽 KPI（全站或本人）
kpi_cols = ["DIAG_DONE", "SHARED", "UNLOCKED", "WON"]
totals = {k: int(col_or_zero(pivot, k, dtype="int64").sum()) for k in kpi_cols}

c1, c2, c3, c4 = st.columns(4)
c1.metric("完成診斷", f"{totals['DIAG_DONE']:,}")
c2.metric("已分享",   f"{totals['SHARED']:,}")
c3.metric("已解鎖",   f"{totals['UNLOCKED']:,}")
c4.metric("回報成交", f"{totals['WON']:,}")

st.divider()

# ---------------- Table ----------------
show_cols = [
    "advisor_name", "advisor_id",
    "DIAG_DONE", "SHARED", "UNLOCKED", "WON",
    "Diagnosed", "Shared", "Unlocked", "Won",
]
existing = [c for c in show_cols if c in pivot.columns]
pivot = pivot[existing].sort_values(by=["WON","UNLOCKED","SHARED","DIAG_DONE"], ascending=False)

st.subheader("顧問事件彙總")
st.dataframe(
    pivot.reset_index(drop=True),
    use_container_width=True,
    hide_index=True,
)

# ---------------- Daily Trend (optional, safe) ----------------
with st.expander("每日事件趨勢（可選）", expanded=False):
    # 建日序列，彙整各事件每日量
    days_index = pd.date_range(start=start_dt.date(), end=end_dt.date(), freq="D")
    df["date"] = pd.to_datetime(df["ts"]).dt.tz_convert(TZ, nonexistent="shift_forward", ambiguous="NaT").dt.date
    daily = (
        df.groupby(["date", "event_type"])
          .size()
          .unstack(fill_value=0)
          .reindex(days_index.date, fill_value=0)
    )
    # 保障欄位
    for col in ["DIAG_DONE","SHARED","UNLOCKED","WON"]:
        if col not in daily.columns:
            daily[col] = 0
    st.line_chart(daily[["DIAG_DONE","SHARED","UNLOCKED","WON"]])
