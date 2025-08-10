# pages/5_Booking.py
import streamlit as st
from pathlib import Path
from src.ui.footer import footer
from src.utils import valid_email, valid_phone, utc_now_iso
from src.repos.bookings import BookingRepo
from src.services.mailer import send_email
from src.config import SMTP, DATA_DIR

st.title("預約 30 分鐘線上會談")
st.info("請留下您的聯絡方式與需求，我們將盡快與您聯繫確認時段。")

# --- 先檢查/建立 data 目錄 ---
try:
    Path(DATA_DIR).mkdir(parents=True, exist_ok=True)
    st.session_state["_data_dir_ok"] = True
except Exception as e:
    st.session_state["_data_dir_ok"] = False
    st.error(f"無法建立資料夾 data/：{e}")

repo = BookingRepo()

# ---- 成功畫面狀態 ----
if "booking_success" not in st.session_state:
    st.session_state.booking_success = False
if "booking_payload" not in st.session_state:
    st.session_state.booking_payload = {}

def show_success_view():
    p = st.session_state.get("booking_payload", {})
    st.success("已收到預約申請，我們將盡快與您聯繫。")
    with st.container(border=True):
        st.markdown(f"**姓名**：{p.get('name','—')}　｜　**Email**：{p.get('email','—')}　｜　**手機**：{p.get('phone','—')}")
        if p.get("ts"): st.caption(f"提交時間（UTC）：{p['ts']}")
    st.divider()
    if st.button("回首頁", use_container_width=True):
        st.switch_page("app.py")

if st.session_state.booking_success:
    show_success_view()
    footer(); st.stop()

# ---- 表單（提交即處理）----
st.subheader("留下您的聯絡方式")
with st.form("book_form", clear_on_submit=False):
    name  = st.text_input("姓名 *")
    phone = st.text_input("手機 *")
    email = st.text_input("Email *")
    notes = st.text_area("需求與背景（選填）")

    disabled = not (name.strip() and phone.strip() and email.strip())
    submit = st.form_submit_button("送出預約申請", disabled=disabled, use_container_width=True)

    if submit:
        # 1) 基本驗證
        errors = []
        if not valid_phone(phone): errors.append("手機格式")
        if not valid_email(email): errors.append("Email 格式")
        if errors:
            st.error("請完成必填欄位或修正格式： " + "、".join(errors))
        else:
            ts = utc_now_iso()

            # 2) 寫入 CSV（一定會做）
            wrote_ok = False
            try:
                repo.add({
                    "ts": ts,
                    "name": name.strip(),
                    "phone": phone.strip(),
                    "email": email.strip(),
                    "notes": (notes or "").strip(),
                    "status": "submitted",
                })
                wrote_ok = True
                st.toast("✅ 已寫入 bookings.csv", icon="✅")
            except Exception as e:
                st.error(f"寫入預約資料時發生錯誤：{e}")

            # 3) 嘗試寄信（寫檔成功才試；失敗不擋流程）
            if wrote_ok:
                # 使用者確認信
                try:
                    ok_user, msg_user = send_email(
                        email.strip(),
                        "已收到您的預約申請｜永傳家族辦公室",
                        f"""
                        <p>{name} 您好，</p>
                        <p>已收到您的 30 分鐘線上會談預約申請，我們將盡快與您聯繫。</p>
                        <ul>
                          <li>時間：收到申請（UTC）{ts}</li>
                          <li>手機：{phone}</li>
                          <li>Email：{email}</li>
                        </ul>
                        <p>若您有補充資訊，歡迎直接回覆此信。</p>
                        <p>— 永傳家族辦公室</p>
                        """,
                        (
                            f"{name} 您好：\n\n已收到您的 30 分鐘線上會談預約申請，我們將盡快與您聯繫。\n"
                            f"- 時間（UTC）：{ts}\n- 手機：{phone}\n- Email：{email}\n\n"
                            "若您有補充資訊，歡迎直接回覆此信。\n— 永傳家族辦公室"
                        ),
                    )
                    if ok_user:
                        st.toast("📫 已寄出客戶確認信", icon="📫")
                    else:
                        st.toast(f"⚠️ 客戶信未寄出：{msg_user}", icon="⚠️")
                except Exception as e:
                    st.toast(f"⚠️ 客戶信寄送錯誤：{e}", icon="⚠️")

                # 管理者通知
                admin_to = SMTP.get("to_admin")
                if admin_to:
                    try:
                        ok_admin, msg_admin = send_email(
                            admin_to,
                            "【新預約】30 分鐘會談申請",
                            f"""
                            <p>收到新的預約申請：</p>
                            <ul>
                              <li>時間（UTC）：{ts}</li>
                              <li>姓名：{name}</li>
                              <li>手機：{phone}</li>
                              <li>Email：{email}</li>
                              <li>備註：{(notes or '（無）')}</li>
                            </ul>
                            """,
                            (
                                "收到新的預約申請：\n"
                                f"- 時間（UTC）：{ts}\n- 姓名：{name}\n- 手機：{phone}\n- Email：{email}\n- 備註：{(notes or '（無）')}\n"
                            ),
                        )
                        if ok_admin:
                            st.toast("📨 已通知管理者", icon="📨")
                        else:
                            st.toast(f"⚠️ 管理者信未寄出：{msg_admin}", icon="⚠️")
                    except Exception as e:
                        st.toast(f"⚠️ 管理者信寄送錯誤：{e}", icon="⚠️")

                # 4) 切換成功畫面
                st.session_state.booking_success = True
                st.session_state.booking_payload = {
                    "ts": ts, "name": name, "phone": phone, "email": email
                }
                st.rerun()

footer()
