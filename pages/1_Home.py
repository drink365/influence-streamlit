# pages/1_Home.py
# Home（穩健跳頁版）
# - 內建 goto()：接受 'pages/5_Booking.py' 或 'Booking' 皆可
# - 找不到頁名時不會拋錯，改顯示備援超連結
# - 提供常用入口按鈕

import sys, pathlib
from datetime import datetime, timezone, timedelta
import streamlit as st

# ---------------- Page & Basics ----------------
st.set_page_config(page_title="首頁 Home", page_icon="🏠", layout="wide")
TZ = timezone(timedelta(hours=8))
now_str = datetime.now(TZ).strftime("%Y-%m-%d %H:%M")

# 顧問資訊（若未登入也能打開，但不會顯示個資）
advisor_name = st.session_state.get("advisor_name", "訪客")
role = st.session_state.get("advisor_role", "guest")

st.title("🏠 首頁 Home")
st.caption(f"現在時間：{now_str}｜使用者：{advisor_name}（{role}）")

st.divider()

# ---------------- Robust Navigation ----------------
def goto(script_path_or_name: str, fallback_label: str | None = None):
    """
    穩健跳頁：可吃 'pages/5_Booking.py' 或 'Booking'。
    1) 先直接嘗試 switch_page(參數)
    2) 失敗則用 get_pages() 把 script_path 對應成 page_name 再跳
    3) 最後嘗試幾種常見名稱變形；仍失敗則給備援超連結
    """
    if not fallback_label:
        fallback_label = "前往指定頁"

    # 1) 直接嘗試（若傳的是正確的 page_name 會成功）
    try:
        st.switch_page(script_path_or_name)
        return
    except Exception:
        pass

    # 2) 利用官方頁面索引把路徑轉名稱
    try:
        from streamlit.source_util import get_pages
        pages = get_pages("")  # 取得所有頁資訊
        sp = script_path_or_name.replace("\\", "/")
        filename = sp.split("/")[-1]
        # 匹配 script_path（完整或檔名）
        for _k, info in pages.items():
            sp_i = info.get("script_path", "").replace("\\", "/")
            if sp_i.endswith(sp) or sp_i.endswith(filename):
                name = info.get("page_name")
                if name:
                    st.switch_page(name)
                    return
    except Exception:
        pass

    # 3) 嘗試名稱變形
    base = script_path_or_name.replace("\\", "/").split("/")[-1].replace(".py", "")
    try_names = [base, base.split("_", 1)[-1], base.replace("_", " ")]
    for name in try_names:
        try:
            st.switch_page(name)
            return
        except Exception:
            continue

    # 4) 備援：顯示可點連結（側欄顯示名通常為去除排序數字與底線的文字）
    st.warning("找不到指定頁面；已提供備援連結：")
    # 盡力推測側欄名稱
    guess = base.split("_", 1)[-1]
    st.markdown(f"➡️ [{fallback_label}]({guess})")

# 也提供一個 QueryString 版（若你需要帶參數）
def goto_with_params(script_path_or_name: str, **params):
    try:
        st.query_params.update(params)
    except Exception:
        pass
    goto(script_path_or_name)

# ---------------- Quick Actions ----------------
st.subheader("📌 快速進入")
c1, c2, c3 = st.columns(3)

with c1:
    st.markdown("#### 🩺 診斷工具")
    st.write("以萬為單位估算遺產稅，並可建立案件。")
    if st.button("開啟 Diagnostic", use_container_width=True):
        goto("pages/2_Diagnostic.py")  # 也可寫 goto("Diagnostic")

with c2:
    st.markdown("#### 📄 結果與報告")
    st.write("查看案件 KPI、下載報告、圖表視覺化。")
    if st.button("開啟 Result", use_container_width=True):
        goto("pages/3_Result.py")  # 或 goto("Result")

with c3:
    st.markdown("#### 📅 預約管理")
    st.write("顧客預約／活動日程（若已建立 Booking 頁）。")
    if st.button("開啟 Booking", use_container_width=True):
        # 你的舊寫法 st.switch_page('pages/5_Booking.py') 會失敗；改用 goto
        goto("pages/5_Booking.py", fallback_label="前往 Booking")

st.divider()

d1, d2 = st.columns(2)
with d1:
    st.markdown("#### 📈 事件儀表板")
    st.write("彙總診斷/分享/解鎖/成交等事件。")
    if st.button("開啟 Events Admin", use_container_width=True):
        goto("pages/7_Events_Admin.py")

with d2:
    st.markdown("#### 📊 顧問 Dashboard")
    st.write("登入後的工作總覽與最近案件清單。")
    if st.button("開啟 Dashboard", use_container_width=True):
        goto("pages/1_Dashboard.py")

st.divider()

# ---------------- Deep Links (可帶參數) ----------------
st.subheader("🔗 進階連結（帶參數示例）")
col_a, col_b = st.columns(2)
with col_a:
    st.text_input("指定案件 ID（可選）", key="home_case_id", placeholder="例如：AB12CD34")
    if st.button("到結果頁（帶 case_id）", use_container_width=True):
        cid = st.session_state.get("home_case_id", "").strip()
        if cid:
            goto_with_params("pages/3_Result.py", case_id=cid)
        else:
            goto("pages/3_Result.py")

with col_b:
    st.text_input("回訪參數（可選）", key="home_ref", placeholder="例如：utm=abc")
    if st.button("到診斷頁（帶自訂參數）", use_container_width=True):
        ref = st.session_state.get("home_ref", "").strip()
        params = {}
        if ref:
            # 只是示範，實際上你可定義任何參數
            params["ref"] = ref
        goto_with_params("pages/2_Diagnostic.py", **params)

st.markdown("---")
st.caption("＊提示：本頁使用穩健跳頁工具 `goto()`，避免 `st.switch_page('pages/xxx.py')` 找不到頁面而報錯。")
