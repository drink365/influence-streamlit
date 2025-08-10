import streamlit as st
import pandas as pd

from src.services.share import create_share
from src.repos.share_repo import ShareRepo
from src.services.auth import is_logged_in, current_role
from src.services.billing import balance, topup

st.set_page_config(page_title="顧問面板", page_icon="🧭", layout="wide")

st.title("🧭 顧問 Dashboard（含點數錢包）")

if not is_logged_in():
    st.warning("此頁需登入。請先到 Login 頁完成 Email OTP 登入。")
    st.page_link("pages/Login.py", label="➡️ 前往登入", icon="🔐")
    st.stop()

advisor_id = st.session_state.get("advisor_id")
advisor_name = st.session_state.get("advisor_name")
role = current_role()

m1, m2 = st.columns(2)
m1.metric("點數餘額", balance(advisor_id))
m2.metric("身份", f"{advisor_name}｜{role}")

st.divider()
with st.form("create_share"):
    st.subheader("建立分享連結")
    case_id = st.text_input("案件碼 Case ID")
    days_valid = st.number_input("有效天數", min_value=1, max_value=90, value=14)
    submitted = st.form_submit_button("建立連結")

if submitted:
    try:
        data = create_share(case_id, advisor_id, days_valid=int(days_valid))
        base_url = st.secrets.get("APP_BASE_URL", "")
        link = (base_url.rstrip('/') + f"/Share?token={data['token']}") if base_url else f"Share?token={data['token']}"
        st.success("已建立連結！")
        st.code(link, language="text")
    except Exception as e:
        st.error(f"建立失敗：{e}")

st.divider()
st.subheader("點數儲值（測試用）")
colA, colB = st.columns(2)
with colA:
    amt = st.number_input("加點數量", min_value=1, max_value=1000, value=20, step=1)
with colB:
    if st.button("加點（測試）"):
        new_bal = topup(advisor_id, int(amt), note="TEST_TOPUP")
        st.success(f"已加點，目前餘額：{new_bal}")

st.divider()
st.subheader("我發出的分享連結")
rows = ShareRepo.list_by_advisor(advisor_id)
if not rows:
    st.info("尚未建立分享連結。")
else:
    base_url = st.secrets.get("APP_BASE_URL", "")
    def make_link(tok: str) -> str:
        return (base_url.rstrip('/') + f"/Share?token={tok}") if base_url else f"Share?token={tok}"
    df = pd.DataFrame([{
        "建立時間": (r.get("created_at") or "")[:19].replace('T',' '),
        "案件碼": r.get("case_id"),
        "連結": make_link(r.get("token")),
        "到期": (r.get("expires_at") or "")[:10],
        "已開啟": bool(r.get("opened_at")),
        "已意向": bool(r.get("accepted_at")),
    } for r in rows])
    st.dataframe(df, use_container_width=True)
