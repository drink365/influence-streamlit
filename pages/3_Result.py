import streamlit as st
from utils.case_repository import CaseRepository

st.set_page_config(page_title="規劃結果", page_icon="📊")

st.title("📊 規劃結果")

case_id = st.session_state.get("case_id")
repo = CaseRepository()

if not case_id:
    st.warning("尚未有可顯示的案例，請先回到首頁填寫資料。")
    st.stop()

case = repo.get_by_case_id(case_id)

if not case:
    st.error("找不到對應的案例資料。")
    st.stop()

st.subheader("📝 基本資料")
st.write(f"- 姓名：**{case.get('name', '')}**")
st.write(f"- 年齡：**{case.get('age', '')} 歲**")
st.write(f"- 性別：**{case.get('gender', '')}**")
st.write(f"- 預算：**{case.get('budget', '')} 萬**")
st.write(f"- 需求：**{case.get('needs', '')}**")

st.subheader("💡 初步規劃建議")

# 交棒流動性需求數字處理
liq_low = case.get('liq_low')
liq_high = case.get('liq_high')

if isinstance(liq_low, (int, float)) and isinstance(liq_high, (int, float)):
    st.write(f"- 交棒流動性需求（估）：**{liq_low:,}–{liq_high:,} 萬**")
else:
    st.write("- 交棒流動性需求（估）：資料不足")

# 其他規劃
suggestions = case.get("suggestions", [])
if suggestions:
    for idx, sug in enumerate(suggestions, start=1):
        st.write(f"{idx}. {sug}")
else:
    st.info("目前尚無具體規劃建議。")

st.markdown("---")
st.write("📌 本結果僅供參考，詳細規劃需與顧問進一步討論。")
