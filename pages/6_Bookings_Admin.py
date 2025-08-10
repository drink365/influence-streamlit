import streamlit as st
import pandas as pd
from src.db import get_conn

st.set_page_config(page_title="預約管理", page_icon="🗂️", layout="wide")

st.title("🗂️ 預約管理（Admin）")
conn = get_conn()

bookings = pd.read_sql_query("SELECT * FROM bookings ORDER BY created_at DESC", conn)
st.dataframe(bookings, use_container_width=True)
