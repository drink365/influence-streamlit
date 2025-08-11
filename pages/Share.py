import streamlit as st
import json

from src.services.share import record_open, record_accept
from src.repos.share_repo import ShareRepo
from src.repos.case_repo import CaseRepo

st.set_page_config(page_title="分享視圖", page_icon="🔗", layout="wide")

st.title("🔗 規劃摘要（分享視圖）")

q = st.query_params
token = q.get("token", "") if isinstance(q.get("token"), str) else (q.get("token")[0] if q.get("token") else "")
if not token:
    st.error("缺少 token。請使用完整分享連結。")
    st.stop()

share = ShareRepo.get_by_token(token)
if not share:
    st.error("連結無效或已被撤銷。請聯絡您的顧問重新取得。")
    st.stop()

# 過期檢查
if ShareRepo.is_expired(share):
    st.error("連結已到期。請聯絡您的顧問重新取得新連結。")
    st.stop()

# 記錄開啟
record_open(token)

case = CaseRepo.get(share["case_id"])
if not case:
    st.error("找不到對應案件。可能已被移除。")
    st.stop()

st.caption(f"案件碼：{case['id']} ｜ 顧問：{case.get('advisor_name','')} ｜ 到期：{(share.get('expires_at') or '')[:10]}")

col = st.columns(3)
col[0].metric("淨遺產（元）", f"{case['net_estate']:,.0f}")
col[1].metric("估算稅額（元）", f"{case['tax_estimate']:,.0f}")
col[2].metric("建議預留稅源（元）", f"{case['liquidity_needed']:,.0f}")

payload = {}
try:
    payload = json.loads(case.get("payload_json") or case.get("plan_json") or "{}")
except Exception:
    payload = {}

with st.expander("更多內容（簡版）", expanded=True):
    st.write("此頁為教育性質示意，僅供討論參考，不構成保險或法律建議。詳細規劃請與顧問預約會議。")
    st.json({
        "規則版本": payload.get("rules_version"),
        "課稅基礎_萬": payload.get("taxable_base_wan"),
        "參數": payload.get("params", {}),
    })

st.divider()

st.subheader("我想要完整方案 ➜")
if st.button("通知顧問，安排完整方案"):
    record_accept(token)
    st.session_state["incoming_case_id"] = case["id"]
    st.success("已通知顧問！請點下方按鈕預約會談。")

st.page_link("pages/4_Booking.py", label="➡️ 前往預約頁（已帶入案件碼）", icon="📅")

st.caption("*隱私說明：此頁僅顯示簡版數據，不包含個資。*")
