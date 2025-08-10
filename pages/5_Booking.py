# pages/5_Booking.py
from datetime import datetime
from zoneinfo import ZoneInfo
import smtplib, ssl
from email.message import EmailMessage
import uuid
import streamlit as st

from src.ui.footer import footer
from src.ui.theme import inject_css
from src.repos.bookings import BookingsRepo, Booking

st.set_page_config(page_title="預約會談", page_icon="📅", layout="wide")
inject_css()
TPE = ZoneInfo("Asia/Taipei")

# ---------- 樣式 ----------
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
              padding:8px 12px; border-radius:10px; font-size:13px; }
</style>
""", unsafe_allow_html=True)

# ---------- 接收結果頁帶來的預填資料 ----------
prefill = st.session_state.pop("booking_prefill", None)

# 先建立預設 keys（僅第一次）
defaults = {
    "booking_case_id": "",
    "booking_name": "",
    "booking_email": "",
    "booking_mobile": "",
    "booking_time": "",
    "booking_need": "",
}
for k, v in defaults.items():
    st.session_state.setdefault(k, v)

# 有預填就覆蓋一次
if prefill:
    if prefill.get("case_id"): st.session_state["booking_case_id"] = prefill["case_id"]
    if prefill.get("name"):    st.session_state["booking_name"]    = prefill["name"]
    if prefill.get("email"):   st.session_state["booking_email"]   = prefill["email"]
    if prefill.get("mobile"):  st.session_state["booking_mobile"]  = prefill["mobile"]
    if prefill.get("need"):    st.session_state["booking_need"]    = prefill["need"]

# ---------- Hero ----------
st.markdown('<div class="yc-hero">', unsafe_allow_html=True)
st.markdown('<span class="yc-badge">預約會談</span>', unsafe_allow_html=True)
st.subheader("留下您的聯絡方式，我們會盡快與您確認時段")
if st.session_state.get("booking_case_id"):
    st.caption(f"個案編號：{st.session_state['booking_case_id']}")
st.markdown("</div>", unsafe_allow_html=True)
st.markdown("<div style='height:12px'></div>", unsafe_allow_html=True)

# ---------- 表單 ----------
st.markdown('<div class="yc-card">', unsafe_allow_html=True)
c1, c2 = st.columns(2)
with c1:
    st.text_input("姓名 *", key="booking_name")
with c2:
    st.text_input("Email *", key="booking_email")

c3, c4 = st.columns(2)
with c3:
    st.text_input("手機 *", key="booking_mobile", placeholder="+886 9xx xxx xxx")
with c4:
    st.text_input("偏好時段（例：本週三 14:00-16:00）", key="booking_time")

st.text_area("需求 *", key="booking_need", height=120, placeholder="請簡述您希望討論的內容…")

# ---------- 驗證 & 送出 ----------
missing = []
if st.session_state["booking_name"].strip() == "":   missing.append("姓名")
if st.session_state["booking_email"].strip() == "":  missing.append("Email")
if st.session_state["booking_mobile"].strip() == "": missing.append("手機")
if st.session_state["booking_need"].strip() == "":   missing.append("需求")

if missing:
    st.markdown("<div class='yc-alert'>尚未完成項目：" + "、".join(missing) + "</div>", unsafe_allow_html=True)

submit = st.button("送出預約申請", type="primary", use_container_width=True, disabled=bool(missing))

def send_mail(subject: str, html_body: str):
    host = st.secrets.get("SMTP_HOST", "")
    port = int(st.secrets.get("SMTP_PORT", "587"))
    user = st.secrets.get("SMTP_USER", "")
    pwd  = st.secrets.get("SMTP_PASS", "")
    mail_from = st.secrets.get("MAIL_FROM", user)
    mail_from_name = st.secrets.get("MAIL_FROM_NAME", "")
    mail_to_admin = st.secrets.get("MAIL_TO_ADMIN", user or mail_from)

    if not (host and port and user and pwd and mail_from and mail_to_admin):
        st.warning("郵件服務未完整設定，已略過寄信（請確認 secrets）")
        return

    msg = EmailMessage()
    msg["Subject"] = subject
    msg["From"] = f"{mail_from_name} <{mail_from}>" if mail_from_name else mail_from
    msg["To"] = mail_to_admin
    msg.set_content("HTML only", subtype="plain")
    msg.add_alternative(html_body, subtype="html")

    if port == 465:
        context = ssl.create_default_context()
        with smtplib.SMTP_SSL(host, port, context=context) as server:
            server.login(user, pwd)
            server.send_message(msg)
    else:
        with smtplib.SMTP(host, port) as server:
            server.starttls()
            server.login(user, pwd)
            server.send_message(msg)

if submit and not missing:
    ts_local = datetime.now(TPE).strftime("%Y-%m-%d %H:%M:%S %Z")
    # 產生 booking_id
    uid = str(uuid.uuid4())[:8].upper()
    booking_id = f"BOOK-{datetime.now(TPE).strftime('%Y%m%d')}-{uid}"

    case_id = st.session_state["booking_case_id"].strip()
    name    = st.session_state["booking_name"].strip()
    email   = st.session_state["booking_email"].strip()
    mobile  = st.session_state["booking_mobile"].strip()
    when    = st.session_state["booking_time"].strip() or "（使用者未填）"
    need    = st.session_state["booking_need"].strip()

    # 1) 寫入 CSV
    repo = BookingsRepo()
    repo.add(Booking(
        booking_id=booking_id,
        ts=ts_local,
        case_id=case_id,
        name=name,
        email=email,
        mobile=mobile,
        preferred_time=when,
        need=need,
        status="new",
    ))

    # 2) 寄出通知信（含個案編號與預約編號）
    admin_html = f"""
    <h3>新的預約申請</h3>
    <p><b>預約編號：</b>{booking_id}</p>
    <p><b>時間：</b>{ts_local}</p>
    <p><b>個案編號：</b>{(case_id or '—')}</p>
    <p><b>姓名：</b>{name}</p>
    <p><b>Email：</b>{email}</p>
    <p><b>手機：</b>{mobile}</p>
    <p><b>偏好時段：</b>{when}</p>
    <p><b>需求：</b><br>{need.replace('\n','<br>')}</p>
    """
    try:
        send_mail(subject=f"【影響力平台】新的預約申請（{booking_id}）", html_body=admin_html)
    except Exception as e:
        st.warning(f"通知信寄送失敗：{e}")

    # 3) 成功訊息 & 清空欄位
    st.success(f"已收到預約申請（編號：{booking_id}），我們將盡快與您聯繫。")
    for k in list(defaults.keys()):
        st.session_state[k] = defaults[k]

    a, b = st.columns([1,1])
    with a:
        if st.button("回首頁", use_container_width=True):
            st.switch_page("app.py")
    with b:
        if st.button("返回診斷", use_container_width=True):
            st.switch_page("pages/2_Diagnostic.py")

st.markdown("</div>", unsafe_allow_html=True)

footer()
