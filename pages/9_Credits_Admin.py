import streamlit as st
import pandas as pd
from io import StringIO

from src.db import get_conn
from src.services.auth import is_logged_in, current_role

st.set_page_config(page_title="點數對帳（Admin）", page_icon="💳", layout="wide")

st.title("💳 對帳與資料匯出（Admin）")

if not is_logged_in() or current_role() != "admin":
    st.error("本頁僅限管理者存取。")
    st.stop()

conn = get_conn()

def _df(sql: str):
    return pd.read_sql_query(sql, conn)

# KPI
w = _df("SELECT * FROM wallets")
tx = _df("SELECT * FROM credit_txns ORDER BY created_at DESC")

c1, c2 = st.columns(2)
c1.metric("顧問數", len(w))
c2.metric("交易筆數", len(tx))

st.markdown("### 錢包餘額")
st.dataframe(w, use_container_width=True)

st.markdown("### 交易明細")
st.dataframe(tx, use_container_width=True)

# 匯出工具

def _download_df(df: pd.DataFrame, name: str):
    csv = StringIO(); df.to_csv(csv, index=False, encoding="utf-8-sig")
    st.download_button(f"⬇️ 匯出{name} CSV", data=csv.getvalue(), file_name=f"{name}.csv", mime="text/csv")

st.divider()
st.markdown("### 匯出資料集")
_download_df(_df("SELECT * FROM cases"), "cases")
_download_df(_df("SELECT * FROM bookings"), "bookings")
_download_df(_df("SELECT * FROM events"), "events")
_download_df(_df("SELECT * FROM shares"), "shares")
_download_df(w, "wallets")
_download_df(tx, "credit_txns")
