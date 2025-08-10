# pages/6_Bookings_Admin.py
import csv
import io
from pathlib import Path
from datetime import datetime, timezone
from zoneinfo import ZoneInfo

import streamlit as st

from src.ui.footer import footer
from src.config import ADMIN_KEY, DATA_DIR

# CSV 欄位定義（加入 admin_notes，與使用者 notes 分離）
HEADERS = ["ts", "name", "phone", "email", "notes", "status", "admin_notes"]
TPE = ZoneInfo("Asia/Taipei")


def _parse_dt_any(s: str):
    """盡量解析我們存的時間格式（台北字串）或過去的 ISO。失敗回 None。"""
    if not s:
        return None
    s = s.strip()
    for fmt in ("%Y-%m-%d %H:%M:%S %Z", "%Y-%m-%d %H:%M:%S"):
        try:
            dt = datetime.strptime(s, fmt)
            if dt.tzinfo is None:
                dt = dt.replace(tzinfo=TPE)
            return dt.astimezone(TPE)
        except Exception:
            pass
    try:
        s2 = s.replace("Z", "+00:00")
        dt = datetime.fromisoformat(s2)
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=timezone.utc)
        return dt.astimezone(TPE)
    except Exception:
        return None


def _read_bookings():
    path = Path(DATA_DIR) / "bookings.csv"
    if not path.exists():
        return [], path
    with path.open("r", newline="", encoding="utf-8") as f:
        rows = list(csv.DictReader(f))
    # 補齊缺欄位避免 KeyError（特別是新加的 admin_notes）
    for r in rows:
        for k in HEADERS:
            r.setdefault(k, "")
    return rows, path


def _write_bookings(rows):
    """直接覆寫 CSV（保留欄位順序，確保 admin_notes 獨立欄位存在）"""
    path = Path(DATA_DIR) / "bookings.csv"
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=HEADERS)
        w.writeheader()
        for r in rows:
            w.writerow({k: r.get(k, "") for k in HEADERS})
    return path


# ----------------- UI -----------------
st.title("預約名單（管理）")

# 狀態與驗證
if "admin_ok" not in st.session_state:
    st.session_state.admin_ok = False

def _verify_sidebar():
    st.session_state.admin_ok = (st.session_state.get("admin_key_sidebar", "") == ADMIN_KEY)
    if st.session_state.admin_ok:
        st.toast("已通過驗證，正在載入資料…", icon="✅")
    else:
        st.toast("密鑰錯誤", icon="❌")

with st.sidebar:
    st.subheader("管理密鑰")
    st.text_input("請輸入管理密鑰", type="password", key="admin_key_sidebar", on_change=_verify_sidebar)

if not st.session_state.admin_ok:
    st.warning("此頁需管理密鑰。")
    footer(); st.stop()

rows, bookings_path = _read_bookings()
if not rows:
    st.info("目前尚無預約資料。")
    footer(); st.stop()

# 預處理：加上台北時間顯示與排序鍵
for r in rows:
    dt = _parse_dt_any(r.get("ts", ""))
    r["_dt_tpe"] = dt
    r["ts_local"] = dt.strftime("%Y-%m-%d %H:%M:%S %Z") if dt else (r.get("ts") or "")

# 篩選條件
st.subheader("篩選條件")
c1, c2 = st.columns([2,1])
with c1:
    kw = st.text_input("關鍵字（姓名 / Email / 手機 / 需求 / 管理備註）", "")
with c2:
    status_opt = ["全部", "submitted", "contacted", "scheduled", "closed"]
    status_pick = st.selectbox("狀態", status_opt, index=0)

c3, c4, c5 = st.columns([1,1,1])
with c3:
    sort_desc = st.toggle("依時間新→舊", value=True)
with c4:
    date_from = st.date_input("起日（台北）", value=None)
with c5:
    date_to = st.date_input("迄日（台北）", value=None)

view = rows

# 關鍵字
if kw:
    lkw = kw.lower()
    def hit(r):
        return (
            lkw in (r.get("name","").lower())
            or lkw in (r.get("email","").lower())
            or lkw in (r.get("phone","").lower())
            or lkw in (r.get("notes","").lower())          # 用戶需求
            or lkw in (r.get("admin_notes","").lower())    # 管理備註
        )
    view = [r for r in view if hit(r)]

# 狀態
if status_pick != "全部":
    view = [r for r in view if (r.get("status") or "").lower() == status_pick]

# 日期區間（以台北時間解析）
if date_from or date_to:
    def in_range(r):
        dt = r.get("_dt_tpe")
        if not dt:
            return False
        ok = True
        if date_from:
            ok = ok and (dt.date() >= date_from)
        if date_to:
            ok = ok and (dt.date() <= date_to)
        return ok
    view = [r for r in view if in_range(r)]

# 排序
view.sort(key=lambda r: (r.get("_dt_tpe") or datetime.min.replace(tzinfo=TPE)), reverse=sort_desc)

# 顯示（區分「需求」與「管理備註」）
st.subheader("名單")
show_cols = ["ts_local", "name", "email", "phone", "status", "notes", "admin_notes"]
st.dataframe([{k: r.get(k, "") for k in show_cols} for r in view],
             use_container_width=True, height=420,
             column_config={
                 "ts_local": "提交時間（台北）",
                 "notes": "需求（用戶填寫）",
                 "admin_notes": "管理備註（內部）",
             })

# 下載（當前篩選結果）
out = io.StringIO()
w = csv.DictWriter(out, fieldnames=HEADERS + ["ts_local"])
w.writeheader()
for r in view:
    row = {k: r.get(k, "") for k in HEADERS}
    row["ts_local"] = r.get("ts_local", "")
    w.writerow(row)
st.download_button("下載目前篩選結果（CSV）", data=out.getvalue().encode("utf-8"),
                   file_name="bookings_filtered.csv", mime="text/csv",
                   use_container_width=True)

# 下載原始 bookings.csv
with bookings_path.open("rb") as f:
    st.download_button("下載全部 bookings.csv", data=f.read(),
                       file_name="bookings.csv", mime="text/csv",
                       use_container_width=True)

st.divider()

# 單筆更新（僅更新狀態與管理備註；不動用戶需求）
st.subheader("單筆更新")
if not view:
    st.info("沒有資料可供更新。")
else:
    # 以「提交時間（台北）＋姓名＋Email」辨識
    options = [
        f"[{r.get('ts_local','')}] {r.get('name','')} / {r.get('email','')}"
        for r in view
    ]
    idx = st.selectbox("選擇一筆紀錄", list(range(len(view))),
                       format_func=lambda i: options[i],
                       key="booking_select_idx")

    target = dict(view[idx])  # 避免直接改 view
    c6, c7 = st.columns(2)
    with c6:
        pick_list = ["submitted", "contacted", "scheduled", "closed"]
        current = (target.get("status") or "submitted")
        new_status = st.selectbox("狀態", pick_list,
                                  index=pick_list.index(current) if current in pick_list else 0,
                                  key=f"status_pick_{idx}")

    # 左側顯示「需求（唯讀）」；右側編輯「管理備註（內部）」
    left, right = st.columns([1,1])
    with left:
        st.markdown("**需求（用戶填寫）**")
        st.text_area("",
                     value=(target.get("notes") or ""),
                     height=160,
                     key=f"user_notes_view_{idx}",
                     disabled=True)
    with right:
        st.markdown("**管理備註（內部）**")
        admin_note_key = f"admin_note_edit_{idx}"
        # 以選取索引作為 key，切換選項時內容會跟著變動
        admin_note_val = st.text_area("",
                                      value=(target.get("admin_notes") or ""),
                                      height=160,
                                      key=admin_note_key,
                                      placeholder="例如：2025-08-10 已致電，安排 8/15 14:00 視訊")

    if st.button("儲存更新", type="primary", use_container_width=True, key=f"save_btn_{idx}"):
        # 把原 rows 找到同一筆（以 ts+email+phone 近似比對）
        def same_row(a, b):
            return (a.get("ts")==b.get("ts") and a.get("email")==b.get("email") and a.get("phone")==b.get("phone"))

        stamp = datetime.now(TPE).strftime("%Y-%m-%d %H:%M:%S %Z")
        for i, r in enumerate(rows):
            if same_row(r, target):
                r["status"] = new_status
                # 覆寫「管理備註」為右側的內容，不再追加到 notes
                r["admin_notes"] = st.session_state.get(admin_note_key, "").strip()
                # 也可選擇自動附帶時間戳：開啟下一行
                # r["admin_notes"] = f"[{stamp}] {r['admin_notes']}" if r["admin_notes"] else ""
                rows[i] = r
                break

        _write_bookings(rows)
        st.success("已更新並寫回 bookings.csv")
        st.toast("✅ 更新完成", icon="✅")
        st.rerun()

footer()
