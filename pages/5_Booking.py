import streamlit as st
from src.ui.footer import footer
from src.utils import valid_email, valid_phone, utc_now_iso
from src.repos.bookings import BookingRepo
from src.services.mailer import send_email

st.title("預約 30 分鐘線上會談")
st.info("（正式版可嵌入 Calendly / Google 日曆 iframe）")

repo = BookingRepo()

with st.form("book", clear_on_submit=False):
    name = st.text_input("姓名 *")
    phone = st.text_input("手機 *")
    email = st.text_input("Email *")
    notes = st.text_area("想先告訴我們的情況（選填）")

    disabled = not (name.strip() and phone.strip() and email.strip())
    submit = st.form_submit_button("送出預約申請", disabled=disabled, use_container_width=True)

if submit:
    errors = []
    if not valid_phone(phone): errors.append("手機格式")
    if not valid_email(email): errors.append("Email 格式")

    if errors:
        st.error("請完成必填欄位或修正格式： " + "、".join(errors))
    else:
        ts = utc_now_iso()
        repo.add({
            "ts": ts,
            "name": name.strip(),
            "phone": phone.strip(),
            "email": email.strip(),
            "notes": (notes or "").strip(),
            "status": "submitted",
        })

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
        ok_user, msg_user = send_email(email.strip(), user_subject, user_html, user_text)

        # 管理者通知（若有設定）
        from src.config import SMTP
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
            ok_admin, msg_admin = send_email(admin_to, admin_subject, admin_html, admin_text)
        else:
            ok_admin, msg_admin = (False, "MAIL_TO_ADMIN not set")

        if ok_user:
            st.success("已收到預約申請，也已寄出確認信到您的 Email。")
        else:
            st.warning("已收到預約申請（寫入完成）。但確認信未寄出（可稍後補寄或檢查 SMTP 設定）。")
        if admin_to:
            st.info("已嘗試通知管理者。" if ok_admin else "管理者通知未寄出，請檢查設定。")

footer()
