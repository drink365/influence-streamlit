# pages/1_Dashboard.py
# 顧問工作台 Dashboard — KPI + 最近案件清單 + 快速連結（用 goto）

import sys, pathlib
from datetime import datetime, timedelta, timezone
import pandas as pd
import streamlit as st
from src.utils.nav import goto, goto_with_params

ROOT = pathlib.Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.append(str(ROOT))

try:
    from src.repos.case_repo import CaseRepo
except Exception:
    CaseRepo = None

TZ = timezone(timedelta(hours=8))
st.set_page_config(page_title="顧問工作台", layout="wide")

advisor_name = st.session_state.get("advisor_name", "顧問")
advisor_id = st.session_state.get("advisor_id", "")
role = st.session_state.get("advisor_role", "user")
is_admin = (role == "admin")

st.title(f"👋 歡迎回來，{advisor_name}！")
st.caption(f"今天是 {datetime.now(TZ).strftime('%Y-%m-%d')}｜身分：{role}")
st.markdown("---")

def _safe_df(rows):
    if rows is None: return pd.DataFrame()
    if isinstance(rows, pd.DataFrame): return rows
    return pd.DataFrame(list(rows))

def _fmt_wan(x) -> str:
    try: return f"{float(x)/10_000:,.1f} 萬元"
    except: return "—"

def _load_cases(limit=50) -> pd.DataFrame:
    if CaseRepo is None:
        return pd.DataFrame(columns=[
            "id","advisor_id","advisor_name","client_alias","status",
            "net_estate","tax_estimate","liquidity_needed","created_at"
        ])
    try:
        rows = CaseRepo.list_latest(limit=limit)
    except Exception:
        rows = []
    df = _safe_df(rows)
    for col in ["id","advisor_id","advisor_name","client_alias","status",
                "net_estate","tax_estimate","liquidity_needed","created_at"]:
        if col not in df.columns: df[col] = None
    if not is_admin and advisor_id:
        df = df[df["advisor_id"] == advisor_id]
    try:
        df["created_at_dt"] = pd.to_datetime(df["created_at"], errors="coerce", utc=True).dt.tz_convert(TZ)
    except Exception:
        df["created_at_dt"] = pd.NaT
    return df.sort_values("created_at_dt", ascending=False)

cases = _load_cases(limit=200)

total_cases = len(cases)
this_month = cases[cases["created_at_dt"].dt.month == datetime.now(TZ).month].shape[0] if total_cases else 0
won_mask = cases["status"].astype(str).str.upper().isin(["WON","成交","WONNED"])
won_count = int(won_mask.sum()) if total_cases else 0

col1, col2, col3 = st.columns(3)
col1.metric("案件總數", f"{total_cases:,}")
col2.metric("本月新增案件", f"{this_month:,}")
col3.metric("回報成交", f"{won_count:,}")

st.markdown("---")

st.subheader("📌 快速進入工具")
qa, qb, qc = st.columns(3)
with qa:
    if st.button("🩺 開始診斷", use_container_width=True):
        goto(st, "pages/2_Diagnostic.py")
with qb:
    if st.button("📄 結果與報告", use_container_width=True):
        goto(st, "pages/3_Result.py")
with qc:
    if st.button("📈 活動管理", use_container_width=True):
        goto(st, "pages/7_Events_Admin.py")

st.markdown("---")

st.subheader("🗂️ 最近案件")
if cases.empty:
    st.info("目前尚無案件。點選「開始診斷」建立第一個案件吧！")
else:
    f1, f2 = st.columns([2,1])
    with f1:
        kw = st.text_input("關鍵字搜尋（案件ID/顧問/客戶別名）", value="")
    with f2:
        status_filter = st.selectbox("狀態篩選", ["全部","Prospect","Won","Lost","Draft"], index=0)

    df = cases.copy()
    if kw:
        k = kw.strip().lower()
        df = df[
            df["id"].astype(str).str.lower().str.contains(k)
            | df["advisor_name"].astype(str).str.lower().str.contains(k)
            | df["client_alias"].astype(str).str.lower().str.contains(k)
        ]
    if status_filter != "全部":
        df = df[df["status"].astype(str).str.title() == status_filter]

    view = pd.DataFrame({
        "建立時間": df["created_at_dt"].dt.strftime("%Y-%m-%d %H:%M"),
        "案件ID": df["id"],
        "顧問": df["advisor_name"].fillna(""),
        "客戶別名": df["client_alias"].fillna(""),
        "淨遺產": df["net_estate"].apply(_fmt_wan),
        "估算稅額": df["tax_estimate"].apply(_fmt_wan),
        "狀態": df["status"].fillna(""),
        "查看": df["id"].apply(lambda cid: f"[開啟](3_Result?case_id={cid})"),
    })

    st.dataframe(view, use_container_width=True, hide_index=True)

st.markdown("---")
st.caption("＊此工作台為概覽頁。金額以『萬元』顯示；詳細內容請至結果頁。")
