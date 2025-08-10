# pages/5_Booking.py
import streamlit as st
from src.ui.footer import footer
from src.utils import valid_email, valid_phone, utc_now_iso
from src.repos.bookings import BookingRepo
from src.services.mailer import send_email
from src.config import SMTP

st.title("預約 30 分鐘線上會談")

# ---- 可選：嵌入排程工具（設定任一就顯示） ----
calendly_url = None
gcal_iframe = None
try:
    calendly_url = st.secrets.get("CALENDLY_URL")
    gcal_iframe = st.secrets.get("GCAL_IFRAME_SRC")
except Exception:
    pass

def render_calendar():
    if calendly_url:
        st.caption("您也可直接在下方日曆中選擇時段（Calendly）")
        st.components.v1.iframe(src=f"{calendly_url}", height=800, scrolling=True)
        return True
    if gcal_iframe:
        st.caption("您也可直接在下方日曆中選擇時段（Google 日曆）")
        st.components.v1.iframe(src=gcal_iframe, height=800, scrolling=True)
        return True
    return False

repo = BookingRepo()

# ---- 狀態：成功後顯示成功畫面（避免重送） ----
if "booking_success" not in st.session_state:
    st.session_state.booking_success = False
if "booking_payload" not in st.session_state:
    st.session_state.booking_payload = {}

def show_success_view():
    payload = st.session_state.get("booking_payload", {})
    st.success("已收到預約申請，我們將盡快與您聯繫。")
    with st.container(border=True):
        st.markdown(
            f"**姓名**：{payload.get('name','—')}　｜　**Email**：{payload.get('email','—')}　｜　**手機**：{payload.get('phone','—')}"
        )
        if payload.get("ts"):
            st.caption(f"提交時間（UTC）：{payload['ts']}")

    st.divider()
    embedded = render_calendar()
    if not embedded:
        st.info("（正式版可嵌入 Calendly / Google 日曆 iframe。請在 Secrets 設定 CALENDLY_URL 或 GCAL_IFRAME_SRC 以啟用。）")

    st.divider()
    c1, c2 = st.columns(2)
    with c1:
        if st.button("回首頁", use_container_width=True):
            st.switch_page("app.py")
    with c2:
        st.write("")  # 保留第二個 CTA 位子（例如 FAQ / 準備清單）
        # 你之後可把這裡改成：st.switch_page("pages/FAQ.py")

if st.session_state.booking_success:
    show_success_view()
    footer()
    st.stop()

# ---- 表單（提交即處理；成功後切換到成功畫面）----
st.subheader("留下您的聯絡方式，我們會回覆您：")
with st.form("book_form", clear_on_submit=False):
    name = st.text_input("姓名 *")
    phone = st.text_input("手機 *")
    email = st.text_input("Email *")
    notes = st.text_area("想先告訴我們的情況（選填）")

    disabled = not (name.strip() and phone.strip() and email.strip())
    submit = st.form_submit_button("送出預約申請", disabled=disabled, use_container_width=True)

    if submit:
        # 1) 格式驗證
        errors = []
        if not valid_phone(phone): errors.append("手機格式")
        if not valid_email(email): errors.append("Email 格式")

        if errors:
            st.error("請完成必填欄位或修正格式： " + "、".join(errors))
        else:
            ts = utc_now_iso()

            # 2) 先寫入 CSV（一定會做）
            repo.add({
                "ts": ts,
                "name": name.strip(),
                "phone": phone.strip(),
                "email": email.strip(),
                "notes": (notes or "").strip(),
                "status": "submitted",
            })

            # 3) 嘗試寄信（SMTP 沒設好不報錯中斷）
            user_subject = "已收到您的預約申請｜永傳家族辦公室"
            user_html = f"""
                <p>{name} 您好，</p>
                <p>已收到您的 30 分鐘線上會談預約申請，我們將盡快與您聯繫。</p>
                <ul>
                  <li>時間：收到申請（UTC）{ts}</li>
                  <li>手機：{phone}</li>
                  <li>Email：{email}</li>
                </ul>
                <p>若您有補充資訊，歡迎直接回覆此信。</p>
                <p>— 永傳家族辦公室</p>
            """
            user_text = (
                f"{name} 您好：\n\n已收到您的 30 分鐘線上會談預約申請，我們將盡快與您聯繫。\n"
                f"- 時間（UTC）：{ts}\n- 手機：{phone}\n- Email：{email}\n\n"
                "若您有補充資訊，歡迎直接回覆此信。\n— 永傳家族辦公室"
            )
            ok_user, msg_user = (False, "SMTP not configured")
            try:
                ok_user, msg_user = send_email(email.strip(), user_subject, user_html, user_text)
            except Exception as e:
                msg_user = str(e)

            admin_to = SMTP.get("to_admin")
            if admin_to:
                admin_subject = "【新預約】30 分鐘會談申請"
                admin_html = f"""
                    <p>收到新的預約申請：</p>
                    <ul>
                      <li>時間（UTC）：{ts}</li>
                      <li>姓名：{name}</li>
                      <li>手機：{phone}</li>
                      <li>Email：{email}</li>
                      <li>備註：{(notes or '（無）')}</li>
                    </ul>
                """
                admin_text = (
                    f"收到新的預約申請：\n"
                    f"- 時間（UTC）：{ts}\n- 姓名：{name}\n- 手機：{phone}\n- Email：{email}\n- 備註：{(notes or '（無）')}\n"
                )
                try:
                    send_email(admin_to, admin_subject, admin_html, admin_text)
                except Exception:
                    pass  # 管理者信失敗不阻斷

            # 4) 切換到成功畫面（避免重送）
            st.session_state.booking_success = True
            st.session_state.booking_payload = {"ts": ts, "name": name, "phone": phone, "email": email}
            # 清空表單（避免返回後又自動帶入）
            st.experimental_rerun()  # 這裡在表單 submit 後可安全使用

# 若需要：在表單上方也能先顯示內嵌日曆
st.divider()
if not (calendly_url or gcal_iframe):
    st.info("（你也可以在 Secrets 設定 CALENDLY_URL 或 GCAL_IFRAME_SRC 來啟用內嵌日曆）")

footer()
