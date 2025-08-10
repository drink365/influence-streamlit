import streamlit as st
from src.ui.theme import inject_css
inject_css()

from pathlib import Path
from datetime import datetime
from zoneinfo import ZoneInfo

from src.ui.footer import footer
from src.utils import valid_email, valid_phone
from src.repos.bookings import BookingRepo
from src.services.mailer import send_email
from src.config import SMTP, DATA_DIR

st.title("預約 30 分鐘線上會談")

# 確保 data/ 目錄存在
try:
    Path(DATA_DIR).mkdir(parents=True, exist_ok=True)
except Exception as e:
    st.error(f"無法建立資料夾 data/：{e}")

repo = BookingRepo()
TPE = ZoneInfo("Asia/Taipei")

# 狀態：是否已送出（送出後隱藏表單）
if "booking_submitted" not in st.session_state:
    st.session_state.booking_submitted = False
if "booking_payload" not in st.session_state:
    st.session_state.booking_payload = {}

def show_success_view():
    p = st.session_state.get("booking_payload", {})
    st.success("已收到預約申請，我們將盡快與您聯繫。")
    with st.container(border=True):
        st.markdown(
            f"**姓名**：{p.get('name','—')}　｜　**Email**：{p.get('email','—')}　｜　**手機**：{p.get('phone','—')}"
        )
        if p.get("ts_local"):
            st.caption(f"提交時間（台北）：{p['ts_local']}")
    st.divider()
    if st.button("回首頁", use_container_width=True):
        st.switch_page("app.py")

if st.session_state.booking_submitted:
    show_success_view()
    footer()
    st.stop()

# 只有在尚未送出時才顯示表單說明
st.info("請留下您的聯絡方式與需求（四項皆為必填），我們將盡快與您聯繫確認時段。")

# 表單（按鈕永遠可按；提交後才檢查）
with st.form("book_form", clear_on_submit=False):
    name    = st.text_input("姓名 *", placeholder="請輸入姓名")
    email   = st.text_input("Email *", placeholder="name@example.com")
    phone   = st.text_input("手機 *", placeholder="09xx xxx xxx")
    request = st.text_area("需求（請簡述想討論的主題）*", placeholder="請至少輸入 10 個字說明您的需求")

    submit = st.form_submit_button("送出預約申請", use_container_width=True)

    if submit:
        # 1) 必填與格式驗證
        missing = []
        if not name.strip():    missing.append("姓名")
        if not email.strip():   missing.append("Email")
        if not phone.strip():   missing.append("手機")
        if not request.strip(): missing.append("需求")

        errors = []
        if email.strip() and not valid_email(email): errors.append("Email 格式")
        if phone.strip() and not valid_phone(phone): errors.append("手機格式")
        if request.strip() and len(request.strip()) < 10: errors.append("需求字數（至少 10 字）")

        if missing:
            st.error("請填寫必填欄位： " + "、".join(missing))
        elif errors:
            st.error("請修正欄位格式： " + "、".join(errors))
        else:
            # 以台北時間記錄與顯示
            ts_local = datetime.now(TPE).strftime("%Y-%m-%d %H:%M:%S %Z")

            # 2) 寫入 CSV（若失敗，顯示錯誤並不進入成功畫面）
            try:
                repo.add({
                    "ts": ts_local,  # 直接存「台北時間字串」
                    "name": name.strip(),
                    "phone": phone.strip(),
                    "email": email.strip(),
                    "notes": request.strip(),
                    "status": "submitted",
                })
                st.toast("✅ 已寫入 bookings.csv", icon="✅")
                wrote_ok = True
            except Exception as e:
                st.error(f"寫入預約資料時發生錯誤：{e}")
                wrote_ok = False

            # 3) 嘗試寄信（寫檔成功才試；SMTP 失敗不阻斷流程）
            if wrote_ok:
                # 客戶確認信
                user_subject = "已收到您的預約申請｜永傳家族辦公室"
                user_html = f"""
                    <p>{name} 您好，</p>
                    <p>已收到您的 30 分鐘線上會談預約申請，我們將盡快與您聯繫。</p>
                    <ul>
                      <li>時間（台北）：{ts_local}</li>
                      <li>手機：{phone}</li>
                      <li>Email：{email}</li>
                    </ul>
                    <p>您填寫的需求：</p>
                    <blockquote>{request.strip()}</blockquote>
                    <p>若您有補充資訊，歡迎直接回覆此信。</p>
                    <p>— 永傳家族辦公室</p>
                """
                user_text = (
                    f"{name} 您好：\n\n已收到您的 30 分鐘線上會談預約申請，我們將盡快與您聯繫。\n"
                    f"- 時間（台北）：{ts_local}\n- 手機：{phone}\n- Email：{email}\n\n"
                    "您填寫的需求：\n"
                    f"{request.strip()}\n\n"
                    "若您有補充資訊，歡迎直接回覆此信。\n— 永傳家族辦公室"
                )
                try:
                    ok_user, msg_user = send_email(email.strip(), user_subject, user_html, user_text)
                    if ok_user:
                        st.toast("📫 已寄出客戶確認信", icon="📫")
                    else:
                        st.toast(f"⚠️ 客戶信未寄出：{msg_user}", icon="⚠️")
                except Exception as e:
                    st.toast(f"⚠️ 客戶信寄送錯誤：{e}", icon="⚠️")

                # 管理者通知（若設定）
                admin_to = SMTP.get("to_admin")
                if admin_to:
                    admin_subject = "【新預約】30 分鐘會談申請"
                    admin_html = f"""
                        <p>收到新的預約申請：</p>
                        <ul>
                          <li>時間（台北）：{ts_local}</li>
                          <li>姓名：{name}</li>
                          <li>手機：{phone}</li>
                          <li>Email：{email}</li>
                        </ul>
                        <p>需求內容：</p>
                        <blockquote>{request.strip()}</blockquote>
                    """
                    admin_text = (
                        "收到新的預約申請：\n"
                        f"- 時間（台北）：{ts_local}\n- 姓名：{name}\n- 手機：{phone}\n- Email：{email}\n\n"
                        "需求內容：\n"
                        f"{request.strip()}\n"
                    )
                    try:
                        ok_admin, msg_admin = send_email(admin_to, admin_subject, admin_html, admin_text)
                        if ok_admin:
                            st.toast("📨 已通知管理者", icon="📨")
                        else:
                            st.toast(f"⚠️ 管理者信未寄出：{msg_admin}", icon="⚠️")
                    except Exception as e:
                        st.toast(f"⚠️ 管理者信寄送錯誤：{e}", icon="⚠️")

                # 4) 切到成功畫面（隱藏表單）
                st.session_state.booking_submitted = True
                st.session_state.booking_payload = {
                    "ts_local": ts_local, "name": name, "phone": phone, "email": email
                }
                st.rerun()

footer()
