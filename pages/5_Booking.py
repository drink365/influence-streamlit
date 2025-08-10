# pages/5_Booking.py
import streamlit as st
from pathlib import Path
from datetime import datetime
from zoneinfo import ZoneInfo

from src.ui.footer import footer
from src.repos.bookings import BookingRepo
from src.services.mailer import send_email
from src.utils import valid_email, valid_phone
from src.config import SMTP, DATA_DIR
from src.ui.theme import inject_css  # 若尚未建立 theme.py，請先加入

# --------- 品牌配色 ----------
PRIMARY = "#BD0E1B"   # 品牌紅
ACCENT  = "#A88716"   # 金色
INK     = "#3C3F46"   # 深灰
BG_SOFT = "#F7F7F8"

st.set_page_config(page_title="預約諮詢｜永傳家族辦公室", page_icon="📅", layout="wide")
inject_css()

# 追加品牌化 CSS
st.markdown(f"""
<style>
  .yc-hero {{
    background: linear-gradient(180deg, {BG_SOFT} 0%, #FFFFFF 100%);
    border: 1px solid rgba(0,0,0,0.04);
    border-radius: 20px;
    padding: 24px 28px;
    box-shadow: 0 8px 30px rgba(0,0,0,0.06);
  }}
  .yc-hero h1 {{ margin: .2rem 0 .5rem; font-size: 30px; color: {INK}; }}
  .yc-hero p {{ color: #555; margin: 0; }}
  .yc-badge {{
    display:inline-block; padding:6px 10px; border-radius:999px;
    background:{ACCENT}14; color:{ACCENT}; font-size:12px; font-weight:700;
    border:1px solid {ACCENT}44; letter-spacing:.3px;
  }}
  .yc-card {{
    background: #fff; border-radius: 16px; padding: 18px 18px;
    border: 1px solid rgba(0,0,0,0.06); box-shadow: 0 6px 22px rgba(0,0,0,0.05);
  }}
  .yc-cta button[kind="primary"] {{
    background:{PRIMARY} !important; border-color:{PRIMARY} !important;
    border-radius: 999px !important; font-weight: 700 !important;
  }}
  .yc-muted {{ color:#666; font-size:13px; }}
  .yc-infobox {{
    margin-top:.8rem; padding:12px 14px; background:#f7f7f8; border-radius:12px;
    border:1px solid rgba(0,0,0,.06);
  }}
  .yc-kv {{ display:flex; gap:.4rem; margin:.2rem 0; }}
  .yc-kv b {{ min-width:64px; color:{INK}; }}
</style>
""", unsafe_allow_html=True)

# --------- Logo + Hero ----------
logo_h = Path("assets/logo-horizontal.png")
logo_v = Path("assets/logo-vertical.png")
logo_src = str(logo_h) if logo_h.exists() else (str(logo_v) if logo_v.exists() else None)

with st.container():
    col_logo, col_title = st.columns([1,2], vertical_alignment="center")
    with col_logo:
        if logo_src:
            st.image(logo_src, use_column_width=True)
    with col_title:
        st.markdown('<div class="yc-hero">', unsafe_allow_html=True)
        st.markdown('<span class="yc-badge">預約諮詢</span>', unsafe_allow_html=True)
        st.markdown("<h1>預約 30 分鐘線上會談</h1>", unsafe_allow_html=True)
        st.markdown("<p>只要 1 分鐘，讓我們更了解您的情況，專人將與您聯繫確認時段。</p>", unsafe_allow_html=True)
        st.markdown("</div>", unsafe_allow_html=True)

st.markdown("<div style='height:12px'></div>", unsafe_allow_html=True)

# --------- 確保 data 目錄存在 ----------
try:
    Path(DATA_DIR).mkdir(parents=True, exist_ok=True)
except Exception as e:
    st.error(f"無法建立資料夾 data/：{e}")

repo = BookingRepo()
TPE = ZoneInfo("Asia/Taipei")

# --------- 成功畫面狀態 ----------
if "booking_submitted" not in st.session_state:
    st.session_state.booking_submitted = False
if "booking_payload" not in st.session_state:
    st.session_state.booking_payload = {}

def success_view():
    p = st.session_state.get("booking_payload", {})
    # 調整顯示順序：姓名/Email/手機/需求 → 最後呈現提交時間（台北）
    st.markdown(f"""
    <div class="yc-card" style="border-left:6px solid {PRIMARY};">
      <h3 style="margin:.2rem 0 .6rem;">已收到您的預約申請</h3>
      <p class="yc-muted">我們將在 1 個工作日內與您聯繫，確認最適合您的時段。</p>
      <div class="yc-infobox">
        <div class="yc-kv"><b>姓名：</b><span>{p.get('name','—')}</span></div>
        <div class="yc-kv"><b>Email：</b><span>{p.get('email','—')}</span></div>
        <div class="yc-kv"><b>手機：</b><span>{p.get('phone','—')}</span></div>
        <div class="yc-kv" style="align-items:flex-start;"><b>需求：</b>
          <span>{(p.get('request') or p.get('notes') or '—').replace('\n','<br>')}</span>
        </div>
        <div class="yc-muted" style="margin-top:.3rem;">提交時間（台北）：{p.get('ts_local','')}</div>
      </div>
    </div>
    """, unsafe_allow_html=True)
    st.markdown("<div style='height:10px'></div>", unsafe_allow_html=True)
    if st.button("回首頁", use_container_width=True):
        st.switch_page("app.py")

if st.session_state.booking_submitted:
    success_view()
    footer()
    st.stop()

# --------- 表單（四欄位必填） ----------
st.markdown('<div class="yc-card">', unsafe_allow_html=True)
st.write("### 聯絡方式")
st.caption("以下四項皆為必填；正確聯絡方式能協助我們更快與您確認時段。")

with st.form("booking_form", clear_on_submit=False):
    c1, c2 = st.columns(2)
    with c1:
        name  = st.text_input("姓名 *", placeholder="請輸入姓名")
        phone = st.text_input("手機 *", placeholder="+886 9xx xxx xxx")
    with c2:
        email   = st.text_input("Email *", placeholder="name@example.com")
        request = st.text_area("需求（請簡述想討論的主題）*", placeholder="請至少輸入 10 個字說明您的需求", height=110)

    st.markdown("<div class='yc-cta'>", unsafe_allow_html=True)
    submit = st.form_submit_button("送出預約申請", type="primary", use_container_width=True)
    st.markdown("</div>", unsafe_allow_html=True)

st.markdown('</div>', unsafe_allow_html=True)

if submit:
    # 必填與格式驗證
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
        ts_local = datetime.now(TPE).strftime("%Y-%m-%d %H:%M:%S %Z")

        # 寫入 CSV（必要）
        try:
            repo.add({
                "ts": ts_local,               # 直接存「台北時間字串」
                "name": name.strip(),
                "phone": phone.strip(),
                "email": email.strip(),
                "notes": request.strip(),     # 用戶需求
                "status": "submitted",
            })
            st.toast("✅ 已寫入 bookings.csv", icon="✅")
            wrote_ok = True
        except Exception as e:
            wrote_ok = False
            st.error(f"寫入預約資料時發生錯誤：{e}")

        # 寄信（寫檔成功才試；失敗不阻斷流程）
        if wrote_ok:
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
                    f"- 時間（台北）：{ts_local}\n"
                    f"- 姓名：{name}\n- 手機：{phone}\n- Email：{email}\n\n"
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

        # 切換到成功畫面（把需求一起存入 session）
        st.session_state.booking_submitted = True
        st.session_state.booking_payload = {
            "ts_local": ts_local,
            "name": name,
            "phone": phone,
            "email": email,
            "request": request.strip()
        }
        st.rerun()

# --------- 頁尾 ----------
footer()
