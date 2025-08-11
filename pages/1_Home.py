# pages/1_Home.py
# 首頁 Home（共用 goto 跳頁）

from datetime import datetime, timezone, timedelta
import streamlit as st
from src.utils.nav import goto, goto_with_params

st.set_page_config(page_title="首頁 Home", page_icon="🏠", layout="wide")
TZ = timezone(timedelta(hours=8))
now_str = datetime.now(TZ).strftime("%Y-%m-%d %H:%M")

advisor_name = st.session_state.get("advisor_name", "訪客")
role = st.session_state.get("advisor_role", "guest")

st.title("🏠 首頁 Home")
st.caption(f"現在時間：{now_str}｜使用者：{advisor_name}（{role}）")
st.divider()

st.subheader("📌 快速進入")
c1, c2, c3 = st.columns(3)

with c1:
    st.markdown("#### 🩺 診斷工具")
    st.write("以萬為單位估算遺產稅，並可建立案件。")
    if st.button("開啟 Diagnostic", use_container_width=True):
        goto(st, "pages/2_Diagnostic.py")  # 或傳 "Diagnostic"

with c2:
    st.markdown("#### 📄 結果與報告")
    st.write("查看案件 KPI、下載報告、圖表視覺化。")
    if st.button("開啟 Result", use_container_width=True):
        goto(st, "pages/3_Result.py")

with c3:
    st.markdown("#### 📅 預約管理")
    st.write("顧客預約／日程（建立後即可使用）。")
    if st.button("開啟 Booking", use_container_width=True):
        goto(st, "pages/5_Booking.py")

st.divider()

d1, d2 = st.columns(2)
with d1:
    st.markdown("#### 📈 事件儀表板")
    st.write("彙總診斷/分享/解鎖/成交等事件。")
    if st.button("開啟 Events Admin", use_container_width=True):
        goto(st, "pages/7_Events_Admin.py")

with d2:
    st.markdown("#### 📊 顧問 Dashboard")
    st.write("登入後的工作總覽與最近案件清單。")
    if st.button("開啟 Dashboard", use_container_width=True):
        goto(st, "pages/1_Dashboard.py")

st.divider()

st.subheader("🔗 進階連結（帶參數示例）")
col_a, col_b = st.columns(2)
with col_a:
    st.text_input("指定案件 ID（可選）", key="home_case_id", placeholder="例如：AB12CD34")
    if st.button("到結果頁（帶 case_id）", use_container_width=True):
        cid = (st.session_state.get("home_case_id") or "").strip()
        if cid:
            goto_with_params(st, "pages/3_Result.py", case_id=cid)
        else:
            goto(st, "pages/3_Result.py")

with col_b:
    st.text_input("回訪參數（可選）", key="home_ref", placeholder="例如：utm=abc")
    if st.button("到診斷頁（帶自訂參數）", use_container_width=True):
        ref = (st.session_state.get("home_ref") or "").strip()
        params = {"ref": ref} if ref else {}
        goto_with_params(st, "pages/2_Diagnostic.py", **params)

st.markdown("---")
st.caption("＊提示：本頁的跳頁使用共用工具 `goto()`，避免 `st.switch_page('pages/xxx.py')` 找不到頁面而報錯。")
