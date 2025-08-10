import streamlit as st
from src.ui.footer import footer
from src.repos.cases import CaseRepo
from src.services.reports import build_docx, build_txt

st.title("診斷結果（簡版）")
repo = CaseRepo()

case_id = st.text_input("輸入 CaseID 查詢", value=st.session_state.get("last_case_id", ""))
if not case_id:
    st.info("尚無資料。請先完成『快速診斷』產生 CaseID。")
    footer(); st.stop()

# 讀取
case = repo.get_by_id(case_id)
if not case:
    st.warning("查無此 CaseID，請確認輸入是否正確。")
    footer(); st.stop()

# 轉型顯示
nums = ["children","equity","real_estate","financial","insurance_cov",
        "total_assets","liq_low","liq_high","gap_low","gap_high"]
for k in nums:
    if case.get(k):
        try: case[k] = int(float(case[k]))
        except: pass
case["focus"] = [x for x in (case.get("focus") or "").split("|") if x]

st.markdown(f"**個案編號：** `{case_id}`  \n**申請人：** {case.get('name') or '（未填）'}")
st.divider()

st.subheader("一、風險重點")
st.write(f"- 資產總額（估）：**{case['total_assets']:,} 萬**")
st.write(f"- 交棒流動性需求（估）：**{case['liq_low']:,}–{case['liq_high']:,} 萬**")
st.write(f"- 現有保單保額：**{case['insurance_cov']:,} 萬**")
st.write(f"- 可能的保障缺口範圍：**{case['gap_low']:,}–{case['gap_high']:,} 萬**")
st.caption("說明：以上為示意試算，實際仍需依照家庭目標、法規與細部資產結構調整。")

st.subheader("二、動作與下載")
c1, c2 = st.columns(2)
with c1:
    if st.button("回到診斷"):
        st.switch_page("pages/2_Diagnostic.py")
with c2:
    docx_bytes = build_docx(case_id, case)
    if docx_bytes:
        st.download_button(
            label="下載簡版報告（.docx）",
            data=docx_bytes,
            file_name=f"{case_id}_report.docx",
            mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
            use_container_width=True
        )
    else:
        txt_bytes = build_txt(case_id, case)
        st.download_button(
            label="下載簡版報告（.txt）",
            data=txt_bytes,
            file_name=f"{case_id}_report.txt",
            mime="text/plain",
            use_container_width=True
        )

footer()
