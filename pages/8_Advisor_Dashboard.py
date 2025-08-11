import streamlit as st
import pandas as pd

from src.services.share import create_share
from src.repos.share_repo import ShareRepo
from src.services.auth import is_logged_in, current_role

st.set_page_config(page_title="顧問面板", page_icon="🧭", layout="wide")

st.title("🧭 顧問 Dashboard")

if not is_logged_in():
    st.warning("此頁需登入。請先到 Login 頁完成 Email OTP 登入。")
    st.page_link("pages/Login.py", label="➡️ 前往登入", icon="🔐")
    st.stop()

advisor_id = st.session_state.get("advisor_id")
advisor_name = st.session_state.get("advisor_name")
role = current_role()

st.caption(f"目前身份：{advisor_name}（{advisor_id}）｜角色：{role}")

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
        "token": r.get("token"),
    } for r in rows])
    st.dataframe(df.drop(columns=["token"]), use_container_width=True)

    # 停用功能
    tok = st.text_input("輸入要停用的 token（從上方連結取值）")
    if st.button("停用該連結") and tok:
        ok = ShareRepo.delete_by_token(tok)
        if ok:
            st.success("已停用（刪除）該分享連結。")
        else:
            st.error("找不到該 token 或已移除。")

st.caption("*提示：停用會直接移除該 token；客戶再開啟將看到『無效或撤銷』訊息。*")
