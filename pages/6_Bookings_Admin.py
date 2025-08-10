# pages/6_Bookings_Admin.py
from __future__ import annotations
from datetime import datetime
from zoneinfo import ZoneInfo
from io import StringIO
import streamlit as st

from src.ui.theme import inject_css
from src.ui.footer import footer
from src.repos.bookings import BookingsRepo

st.set_page_config(page_title="預約管理後台", page_icon="🗂️", layout="wide")
inject_css()
TPE = ZoneInfo("Asia/Taipei")

# ---------------- 樣式 ----------------
st.markdown("""
<style>
  .yc-card { background:#fff; border-radius:16px; padding:18px;
             border:1px solid rgba(0,0,0,.06); box-shadow:0 6px 22px rgba(0,0,0,.05); }
  .yc-hero { background:linear-gradient(180deg,#F7F7F8 0%,#FFF 100%);
             border-radius:20px; padding:24px 28px; }
  .yc-badge { display:inline-block; padding:6px 10px; border-radius:999px;
              background:rgba(168,135,22,0.14); color:#A88716; font-size:12px; font-weight:700;
              border:1px solid rgba(168,135,22,0.27); }
  .yc-alert { background:#fff9f0; border:1px solid #facc15; color:#92400e;
              padding:8px 12px; border-radius:10px; font-size:13px; border-radius:10px; }
  .pill { display:inline-block; padding:2px 8px; border-radius:999px; font-size:12px; margin-right:6px; }
  .pill-new { background:#fef3c7; color:#92400e; border:1px solid #fcd34d; }
  .pill-contacted { background:#e0f2fe; color:#075985; border:1px solid #7dd3fc; }
  .pill-scheduled { background:#ecfccb; color:#365314; border:1px solid #bef264; }
  .pill-done { background:#e9ffe7; color:#166534; border:1px solid #86efac; }
  .pill-cancelled { background:#fee2e2; color:#991b1b; border:1px solid #fca5a5; }
</style>
""", unsafe_allow_html=True)

# ---------------- 登入驗證 ----------------
st.markdown('<div class="yc-hero">', unsafe_allow_html=True)
st.markdown('<span class="yc-badge">管理後台</span>', unsafe_allow_html=True)
st.subheader("預約管理")
st.caption("僅限內部使用。")
st.markdown("</div>", unsafe_allow_html=True)
st.markdown("<div style='height:12px'></div>", unsafe_allow_html=True)

expected_pass = st.secrets.get("BOOKINGS_ADMIN_PASS") or st.secrets.get("ADMIN_PASS") or ""
if not expected_pass:
    st.warning("尚未設定管理密碼（請於 Secrets 設定 `BOOKINGS_ADMIN_PASS` 或 `ADMIN_PASS`）。")
    footer(); st.stop()

pw_col, _ = st.columns([1, 4])
with pw_col:
    pwd = st.text_input("管理密碼", type="password", key="bookings_admin_pw")
    if st.button("登入", use_container_width=True):
        if pwd == expected_pass:
            st.session_state["bookings_admin_authed"] = True
            st.rerun()
        else:
            st.error("密碼錯誤。")

if not st.session_state.get("bookings_admin_authed"):
    footer(); st.stop()

# ---------------- 資料存取 ----------------
repo = BookingsRepo()
rows = repo.list_all()  # List[Dict]

# 標準化/排序（預設照建立時間新到舊）
def parse_ts(s: str):
    try:
        return datetime.strptime(s, "%Y-%m-%d %H:%M:%S %Z")
    except Exception:
        return datetime.min.replace(tzinfo=TPE)

rows.sort(key=lambda r: parse_ts(r.get("ts", "")), reverse=True)

# ---------------- 篩選/搜尋列 ----------------
with st.container():
    f1, f2, f3, f4 = st.columns([1.8, 2.2, 1.2, 1.2])
    with f1:
        q = st.text_input("搜尋（姓名 / Email / 手機 / 個案編號 / 預約編號）", key="bk_q")
    with f2:
        all_status = ["new", "contacted", "scheduled", "done", "cancelled"]
        def_status = ["new", "contacted", "scheduled"]
        status_sel = st.multiselect("狀態", options=all_status, default=def_status, key="bk_status_sel")
    with f3:
        sort_opt = st.selectbox("排序", ["建立時間（新→舊）", "建立時間（舊→新）"], index=0)
    with f4:
        show_limit = st.number_input("每頁筆數", min_value=10, max_value=200, step=10, value=50)

def match_row(r: dict, q: str) -> bool:
    if not q: return True
    q = q.lower().strip()
    for k in ["booking_id", "case_id", "name", "email", "mobile", "preferred_time", "need"]:
        v = (r.get(k) or "").lower()
        if q in v:
            return True
    return False

# 篩選
filtered = [r for r in rows if r.get("status") in status_sel and match_row(r, q)]

# 排序
if sort_opt == "建立時間（舊→新）":
    filtered = list(reversed(filtered))

# 分頁
total = len(filtered)
page = st.session_state.get("bk_page", 1)
max_page = max(1, (total + show_limit - 1) // show_limit)
page = min(max(page, 1), max_page)
st.session_state["bk_page"] = page
start = (page - 1) * show_limit
end = start + show_limit
page_rows = filtered[start:end]

# ---------------- 清單 ----------------
st.markdown('<div class="yc-card">', unsafe_allow_html=True)
st.markdown(f"**共 {total} 筆**（第 {page} / {max_page} 頁）")

# 簡易標籤
def badge(s: str) -> str:
    cls = {
        "new": "pill-new",
        "contacted": "pill-contacted",
        "scheduled": "pill-scheduled",
        "done": "pill-done",
        "cancelled": "pill-cancelled",
    }.get(s, "pill")
    return f"<span class='pill {cls}'>{s}</span>"

# 表格（精簡欄位）
import pandas as pd
tbl = pd.DataFrame([
    {
        "預約編號": r.get("booking_id", ""),
        "時間": r.get("ts", ""),
        "狀態": r.get("status", ""),
        "姓名": r.get("name", ""),
        "Email": r.get("email", ""),
        "手機": r.get("mobile", ""),
        "個案編號": r.get("case_id", ""),
        "偏好時段": r.get("preferred_time", ""),
    }
    for r in page_rows
])

st.dataframe(
    tbl,
    use_container_width=True,
    hide_index=True,
)

# 分頁控制
c_prev, c_info, c_next = st.columns([1, 4, 1])
with c_prev:
    if st.button("上一頁", disabled=(page <= 1), use_container_width=True):
        st.session_state["bk_page"] = max(1, page - 1)
        st.rerun()
with c_info:
    st.caption(f"顯示 {start+1}-{min(end, total)} / 共 {total}")
with c_next:
    if st.button("下一頁", disabled=(page >= max_page), use_container_width=True):
        st.session_state["bk_page"] = min(max_page, page + 1)
        st.rerun()

# 匯出 CSV（匯出目前篩選結果）
csv_buf = StringIO()
pd.DataFrame(filtered).to_csv(csv_buf, index=False, encoding="utf-8")
st.download_button(
    "下載目前篩選結果（CSV）",
    data=csv_buf.getvalue().encode("utf-8"),
    file_name=f"bookings_filtered_{datetime.now(TPE).strftime('%Y%m%d_%H%M')}.csv",
    mime="text/csv",
    use_container_width=True,
)
st.markdown("</div>", unsafe_allow_html=True)

st.markdown("<div style='height:12px'></div>", unsafe_allow_html=True)

# ---------------- 詳細 / 狀態更新 ----------------
st.markdown('<div class="yc-card">', unsafe_allow_html=True)
st.markdown("### 詳細與狀態更新")

if not page_rows:
    st.info("目前沒有符合條件的預約。")
else:
    ids = [r.get("booking_id", "") for r in page_rows]
    idx = st.selectbox("選擇一筆預約編號", options=ids, index=0)
    cur = next((r for r in page_rows if r.get("booking_id") == idx), None)

    if cur:
        st.markdown("---")
        c1, c2 = st.columns(2)
        with c1:
            st.write(f"**預約編號**：{cur.get('booking_id','')}")
            st.write(f"**建立時間**：{cur.get('ts','')}")
            st.write(f"**個案編號**：{cur.get('case_id','—') or '—'}")
            st.write(f"**姓名**：{cur.get('name','')}")
            st.write(f"**Email**：{cur.get('email','')}")
            st.write(f"**手機**：{cur.get('mobile','')}")
            st.write(f"**偏好時段**：{cur.get('preferred_time','') or '—'}")
        with c2:
            st.write("**需求**：")
            st.markdown(f"<div style='white-space:pre-wrap'>{(cur.get('need') or '').strip()}</div>", unsafe_allow_html=True)

        st.markdown("---")
        st.write("**更新狀態**")
        new_status = st.radio(
            "選擇新的狀態",
            options=["new", "contacted", "scheduled", "done", "cancelled"],
            index=["new", "contacted", "scheduled", "done", "cancelled"].index(cur.get("status","new")),
            horizontal=True,
            key="bk_status_radio",
        )
        act_cols = st.columns([1,1,4])
        with act_cols[0]:
            if st.button("儲存狀態", type="primary", use_container_width=True):
                ok = repo.update_status(cur.get("booking_id",""), new_status)
                if ok:
                    st.success("已更新狀態。")
                    st.rerun()
                else:
                    st.error("更新失敗，請稍後再試。")
        with act_cols[1]:
            if st.button("回到清單頂部", use_container_width=True):
                st.session_state["bk_page"] = 1
                st.rerun()

st.markdown("</div>", unsafe_allow_html=True)

footer()
