import streamlit as st
import pandas as pd
from io import StringIO

from src.db import get_conn
from src.services.auth import is_logged_in, current_role

st.set_page_config(page_title="點數對帳（Admin）", page_icon="💳", layout="wide")

st.title("💳 點數對帳（Admin）")

if not is_logged_in() or current_role() != "admin":
    st.error("本頁僅限管理者存取。")
    st.stop()

conn = get_conn()

df_wallets = pd.read_sql_query("SELECT * FROM wallets", conn)
df_tx = pd.read_sql_query("SELECT * FROM credit_txns ORDER BY created_at DESC", conn)

c1, c2 = st.columns(2)
c1.metric("顧問數", len(df_wallets))
c2.metric("交易筆數", len(df_tx))

st.markdown("### 錢包餘額")
st.dataframe(df_wallets, use_container_width=True)

st.markdown("### 交易明細")
st.dataframe(df_tx, use_container_width=True)

csv = StringIO()
df_tx.to_csv(csv, index=False, encoding="utf-8-sig")
st.download_button("⬇️ 匯出交易 CSV", data=csv.getvalue(), file_name="credit_txns.csv", mime="text/csv")
