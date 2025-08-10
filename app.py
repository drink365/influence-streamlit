import streamlit as st
import pandas as pd
import numpy as np
from datetime import datetime

# 頁面設定
st.set_page_config(page_title="《影響力》傳承策略平台", page_icon="📦", layout="wide")

# 側邊選單
menu = st.sidebar.radio(
    "功能選單",
    ("首頁", "資料上傳與檢視", "數據分析", "關於平台")
)

# --- 頁面內容 ---
if menu == "首頁":
    st.title("📦 《影響力》傳承策略平台")
    st.write("歡迎使用此平台，這裡將整合多種工具，協助您規劃退休與傳承策略。")
    st.info("請使用左側功能選單切換不同工具。")

elif menu == "資料上傳與檢視":
    st.header("資料上傳與檢視")
    uploaded_file = st.file_uploader("請上傳 CSV 檔案", type="csv")
    if uploaded_file is not None:
        df = pd.read_csv(uploaded_file)
        st.dataframe(df)

elif menu == "數據分析":
    st.header("數據分析範例")
    chart_data = pd.DataFrame(
        np.random.randn(20, 3),
        columns=['A', 'B', 'C']
    )
    st.line_chart(chart_data)

elif menu == "關於平台":
    st.header("關於平台")
    st.markdown("""
    《影響力》傳承策略平台由永傳家族辦公室開發，
    旨在提供高資產家庭與企業主專業的退休與財富傳承規劃工具。
    """)

# --- 聯絡資訊（所有頁面共用） ---
st.markdown("---")
st.markdown(
    """
    <div style='display: flex; justify-content: center; align-items: center; gap: 1.5em; font-size: 14px; color: gray;'>
      <a href='?' style='color:#006666; text-decoration: underline;'>《影響力》傳承策略平台</a>
      <a href='https://gracefo.com' target='_blank'>永傳家族辦公室</a>
      <a href='mailto:123@gracefo.com'>123@gracefo.com</a>
    </div>
    """,
    unsafe_allow_html=True
)
