# pages/6_Bookings_Admin.py
import csv
from pathlib import Path
from datetime import datetime, timezone
from zoneinfo import ZoneInfo

import streamlit as st

from src.ui.footer import footer
from src.config import ADMIN_KEY, DATA_DIR
from src.utils import EMAIL_RE, PHONE_RE  # 若要用到驗證可調用
# 目前 repos.BookingRepo 沒有 update/save_all，這頁面自行處理 CSV 輸出入
HEADERS = ["ts", "name", "phone", "email", "notes", "status"]

TPE = ZoneInfo("Asia/Taipei")


def _parse_dt_any(s: str):
    """盡量解析我們存的時間格式（台北時間字串）或過去的 ISO 格式。失敗回 None。"""
    if not s:
        return None
    s = s.strip()
    # 先試人類可讀（台北）: 2025-08-10 21:15:01 TST / CST
    for fmt in ("%Y-%m-%d %H:%M:%S %Z", "%Y-%m-%d %H:%M:%S"):
        try:
            dt = datetime.strptime(s, fmt)
            if dt.tzinfo is None:
                dt = dt.replace(tzinfo=TPE)
            return dt.astimezone(TPE)
        except Exception:
            pass
    # 再試 ISO（可能是 UTC）
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
    # 補齊缺欄位避免 KeyError
    for r in rows:
        for k in HEADERS:
            r.setdefault(k, "")
    return rows, path


def _write_bookings(rows):
    """直接覆寫 CSV（保留欄位順序）"""
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
    kw = st.text_input("關鍵字（姓名 / Email / 手機 / 需求）", "")
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
            or lkw in (r.get("notes","").lower())
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

# 顯示
st.subheader("名單")
show_cols = ["ts_local", "name", "email", "phone", "status", "notes"]
st.dataframe([{k: r.get(k, "") for k in show_cols} for r in view],
             use_container_width=True, height=420,
             column_config={"ts_local": "提交時間（台北）"})

# 下載（當前篩選結果）
import io
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

# 單筆更新（狀態 / 管理備註）
st.subheader("單筆更新")
if not view:
    st.info("沒有資料可供更新。")
else:
    # 用「提交時間（台北）＋姓名＋Email」幫你辨識
    options = [
        f"[{r.get('ts_local','')}] {r.get('name','')} / {r.get('email','')}"
        for r in view
    ]
    idx = st.selectbox("選擇一筆紀錄", list(range(len(view))),
                       format_func=lambda i: options[i])

    target = dict(view[idx])  # 避免直接改 view
    c6, c7 = st.columns(2)
    with c6:
        new_status = st.selectbox("狀態",
                                  ["submitted", "contacted", "scheduled", "closed"],
                                  index=["submitted", "contacted", "scheduled", "closed"].index((target.get("status") or "submitted")))
    with c7:
        admin_note = st.text_area("管理備註（會寫回 notes 欄位後段）", value="", height=100,
                                  placeholder="例如：2025-08-10 已致電，安排 8/15 14:00 視訊")

    if st.button("儲存更新", type="primary", use_container_width=True):
        # 把原 rows 找到同一筆（以 ts+email+phone 近似比對；若重複再以 index 輔助）
        def same_row(a, b):
            return (a.get("ts")==b.get("ts") and a.get("email")==b.get("email") and a.get("phone")==b.get("phone"))

        # 準備寫回：在 notes 後面追加管理備註，附加時間戳（台北）
        stamp = datetime.now(TPE).strftime("%Y-%m-%d %H:%M:%S %Z")
        for i, r in enumerate(rows):
            if same_row(r, target):
                r["status"] = new_status
                # 以分隔線追加備註
                if admin_note.strip():
                    base = r.get("notes","").strip()
                    extra = f"\n---\n[{stamp}] 管理備註：{admin_note.strip()}" if base else f"[{stamp}] 管理備註：{admin_note.strip()}"
                    r["notes"] = (base + extra)
                rows[i] = r
                break
        _write_bookings(rows)
        st.success("已更新並寫回 bookings.csv")
        st.toast("✅ 更新完成", icon="✅")
        st.experimental_rerun()

footer()
