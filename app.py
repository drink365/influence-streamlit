import streamlit as st
import sys, platform

st.set_page_config(page_title="影響力 - Smoke Test", page_icon="✅", layout="centered")

st.title("✅ Streamlit Smoke Test")
st.write("如果你看到這頁，代表部署成功。接下來再逐步加回功能。")

st.subheader("Runtime")
st.write("Python:", sys.version)
st.write("Platform:", platform.platform())

st.subheader("互動測試")
x = st.number_input("輸入數字", 0, 100, 10)
st.write("x * 2 =", x * 2)
