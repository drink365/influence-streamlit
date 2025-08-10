import streamlit as st
import pandas as pd
from io import BytesIO
from datetime import datetime
import uuid
from pathlib import Path
from docx import Document
from docx.shared import Pt

# ========== 基本設定 ==========
st.set_page_config(page_title="影響力平台", page_icon="✨", layout="wide")

DATA_DIR = Path("data")
DATA_DIR.mkdir(parents=True, exist_ok=True)
CASES_CSV = DATA_DIR / "cases.csv"

# 初始化狀態
if "cases" not in st.session_state:
    st.session_state.cases = {}
if "last_case_id" not in st.session_state:
    st.session_state.last_case_id = ""
if "page" not in st.session_state:
    st.session_state.page = "首頁"

# ========== 共用：頁尾 ==========
def footer():
    st.markdown("---")
    st.markdown(
        """
        <div style='display: flex; justify-content: center; align-items: center; gap: 1.5em; font-size: 14px; color: gray;'>
          <a href='?' style='color:#006666; text-decoration: underline;'>《影響力》傳承策略平台</a>
          <a href='https://gracefo.com' target='_blank'>永傳家族辦公室</a>
          <a href='mailto:123@gracefo.com'>123@gracefo.com</a>
        </div>
        """,
        unsafe_allow_html=True
    )

# ========== 工具函式 ==========
def save_case_to_csv(case_id: str, payload: dict):
    df_new = pd.DataFrame([{**payload, "case_id": case_id}])
    if CASES_CSV.exists():
        df_old = pd.read_csv(CASES_CSV)
        df_all = pd.concat([df_old, df_new], ignore_index=True)
    else:
        df_all = df_new
    df_all.to_csv(CASES_CSV, index=False)

def load_case_from_csv(case_id: str):
    if not CASES_CSV.exists():
        return None
    df = pd.read_csv(CASES_CSV)
    m = df[df["case_id"] == case_id]
    if m.empty:
        return None
    row = m.iloc[-1].to_dict()
    # 轉型
    for k in ["equity","real_estate","financial","insurance_cov","total_assets","liq_low","liq_high","gap_low","gap_high","children"]:
        if k in row and pd.notna(row[k]):
            row[k] = int(float(row[k]))
    if "focus" in row and isinstance(row["focus"], str):
        row["focus"] = [s for s in row["focus"].split("|") if s]
    return row

def make_docx_report(case_id: str, case: dict) -> bytes:
    doc = Document()
    styles = doc.styles['Normal']
    styles.font.name = 'Microsoft JhengHei'
    styles.font.size = Pt(11)

    doc.add_heading("影響力平台｜傳承規劃簡版報告", level=1)
    doc.add_paragraph(f"個案編號：{case_id}")
    doc.add_paragraph(f"建立時間：{datetime.utcnow().strftime('%Y-%m-%d %H:%M UTC')}")

    doc.add_heading("一、基本資料", level=2)
    p = doc.add_paragraph()
    p.add_run(f"申請人：{case.get('name') or '（未填）'}　")
    p.add_run(f"婚姻：{case.get('marital','')}　子女：{case.get('children','')}　")
    p.add_run(f"特殊照顧對象：{case.get('special','')}")

    doc.add_heading("二、資產概況（估）", level=2)
    doc.add_paragraph(f"- 公司股權：{case['equity']:,} 萬")
    doc.add_paragraph(f"- 不動產：{case['real_estate']:,} 萬")
    doc.add_paragraph(f"- 金融資產：{case['financial']:,} 萬")
    doc.add_paragraph(f"- 既有保單保額：{case['insurance_cov']:,} 萬")
    doc.add_paragraph(f"- 資產總額（估）：{case['total_assets']:,} 萬")

    doc.add_heading("三、交棒流動性與保障缺口（示意）", level=2)
    doc.add_paragraph(f"- 交棒流動性需求（估）：{case['liq_low']:,} – {case['liq_high']:,} 萬")
    doc.add_paragraph(f"- 可能的保障缺口：{case['gap_low']:,} – {case['gap_high']:,} 萬")

    doc.add_heading("四、您的重點關注", level=2)
    focuses = case.get("focus") or []
    if focuses:
        for f in focuses:
            doc.add_paragraph(f"• {f}")
    else:
        doc.add_paragraph("（未填）")

    doc.add_heading("五、初步建議（草案）", level=2)
    bullets = [
        "以保單建立緊急流動性池，避免交棒時資金壓力。",
        "評估是否需要信託來管理特殊照顧對象或特定資產的分配節奏。",
        "針對股權與不動產，規劃適當的傳承順序與治理安排。",
        "視需要規劮遺囑，確保意願清楚、減少爭議。",
    ]
    for b in bullets:
        doc.add_paragraph(f"• {b}")

    doc.add_paragraph("\n免責聲明：本報告內容為初步示意，實際方案須由專業顧問複核並依相關法令辦理。")

    bio = BytesIO()
    doc.save(bio)
    return bio.getvalue()

# ========== 頁面 ==========
def page_home():
    st.title("傳承您的影響力")
    st.write("AI 智慧 + 專業顧問，打造專屬的可視化傳承方案，確保財富與愛同時流傳。")

    c1, c2, c3 = st.columns(3)
    with c1:
        st.markdown("### 家族資產地圖\n將股權、不動產、保單、金融資產一次整理")
    with c2:
        st.markdown("### AI 傳承策略\n根據家族偏好與資料生成個人化方案")
    with c3:
        st.markdown("### 行動計劃表\n明確列出下一步與時間表，陪伴落地")

    st.divider()
    st.subheader("立即行動")
    a, b = st.columns(2)
    with a:
        if st.button("開始規劃（免費）", use_container_width=True):
            st.session_state.page = "診斷"
            st.rerun()
    with b:
        if st.button("預約 30 分鐘諮詢", use_container_width=True):
            st.session_state.page = "預約"
            st.rerun()

    st.caption("免責：本平台提供之計算與建議僅供初步規劃參考，請依專業顧問複核與相關法令為準。")

    # Footer
    footer()

def page_diagnostic():
    st.title("傳承規劃｜快速診斷（MVP）")
    st.write("填寫 60 秒，取得初步風險指標與行動建議。")

    with st.form("diag"):
        st.subheader("家庭結構")
        c1, c2, c3 = st.columns(3)
        marital = c1.selectbox("婚姻狀態", ["未婚", "已婚", "離異", "喪偶"])
        children = c2.number_input("子女數", min_value=0, max_value=10, step=1, value=2)
        special = c3.selectbox("是否有特殊照顧對象", ["否", "是"])

        st.subheader("資產概況（估算即可，單位：萬元）")
        c4, c5 = st.columns(2)
        equity = c4.number_input("公司股權估值", min_value=0, step=100, value=5000)
        real_estate = c5.number_input("不動產估值", min_value=0, step=100, value=8000)
        c6, c7 = st.columns(2)
        financial = c6.number_input("金融資產估值", min_value=0, step=100, value=3000)
        insurance_cov = c7.number_input("既有保單保額", min_value=0, step=100, value=2000)

        st.subheader("您的重點關注（可多選）")
        focus = st.multiselect(
            "選擇重點",
            ["稅務負擔", "現金流穩定", "交棒安排", "家族和諧", "跨境安排"],
            default=["現金流穩定", "交棒安排"]
        )

        st.subheader("聯絡方式")
        c8, c9 = st.columns(2)
        name = c8.text_input("姓名")
        mobile = c9.text_input("手機")
        email = st.text_input("Email")

        submitted = st.form_submit_button("產生診斷結果與 CaseID")
        if submitted:
            case_id = "YC-" + uuid.uuid4().hex[:6].upper()
            total_assets = equity + real_estate + financial
            liq_low = round(total_assets * 0.10)
            liq_high = round(total_assets * 0.20)
            gap_low = max(0, liq_low - insurance_cov)
            gap_high = max(0, liq_high - insurance_cov)

            payload = {
                "ts": datetime.utcnow().isoformat(),
                "name": name, "mobile": mobile, "email": email,
                "marital": marital, "children": int(children), "special": special,
                "equity": int(equity), "real_estate": int(real_estate), "financial": int(financial),
                "insurance_cov": int(insurance_cov),
                "focus": "|".join(focus),
                "total_assets": int(total_assets),
                "liq_low": int(liq_low), "liq_high": int(liq_high),
                "gap_low": int(gap_low), "gap_high": int(gap_high),
            }

            # 寫入 session 與 CSV
            st.session_state.cases[case_id] = {**payload, "focus": focus}
            save_case_to_csv(case_id, payload)

            st.session_state.last_case_id = case_id
            st.success(f"已建立個案：{case_id}")
            if st.button("查看診斷結果 ➜"):
                st.session_state.page = "結果"
                st.rerun()

    # Footer
    footer()

def page_result():
    st.title("診斷結果（簡版）")
    case_id = st.text_input("輸入 CaseID 查詢", value=st.session_state.get("last_case_id", ""))

    # 先從記憶體拿；沒有就從 CSV 載
    case = st.session_state.cases.get(case_id) or load_case_from_csv(case_id)
    if not case:
        st.info("尚無資料。請先完成『快速診斷』產生 CaseID。")
        footer()
        return

    st.markdown(f"**個案編號：** `{case_id}`  \n**申請人：** {case.get('name') or '（未填）'}")
    st.divider()

    st.subheader("一、風險重點")
    st.write(f"- 資產總額（估）：**{case['total_assets']:,} 萬**")
    st.write(f"- 交棒流動性需求（估）：**{case['liq_low']:,}–{case['liq_high']:,} 萬**")
    st.write(f"- 現有保單保額：**{case['insurance_cov']:,} 萬**")
    st.write(f"- 可能的保障缺口範圍：**{case['gap_low']:,}–{case['gap_high']:,} 萬**")
    st.caption("說明：以上為示意試算，實際仍需依照家庭目標、法規與細部資產結構調整。")

    st.subheader("二、可行方向（草案）")
    bullets = [
        "以保單建立緊急流動性池，避免交棒時資金壓力。",
        "評估是否需要信託來管理特殊照顧對象或特定資產的分配節奏。",
        "針對股權與不動產，規劃適當的傳承順序與治理安排。",
        "視需要規劃遺囑，確保意願清楚、減少爭議。",
    ]
    for b in bullets:
        st.write(f"- {b}")

    st.subheader("三、動作與下載")
    c1, c2 = st.columns(2)
    with c1:
        if st.button("預約 30 分鐘諮詢"):
            st.session_state.page = "預約"
            st.rerun()
    with c2:
        docx_bytes = make_docx_report(case_id, case)
        st.download_button(
            label="下載簡版報告（.docx）",
            data=docx_bytes,
            file_name=f"{case_id}_report.docx",
            mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
            use_container_width=True
        )

    # Footer
    footer()

def page_book():
    st.title("預約 30 分鐘線上會談")
    st.info("（正式版可嵌入 Calendly / Google 日曆 iframe）")
    with st.form("book"):
        name = st.text_input("姓名")
        phone = st.text_input("手機")
        email = st.text_input("Email")
        notes = st.text_area("想先告訴我們的情況（選填）")
        if st.form_submit_button("送出預約申請"):
            st.success("已收到預約申請，我們將盡快與您聯繫。")

    # Footer
    footer()

def page_advisors():
    st.title("顧問專區（MVP）")
    st.write("先上線最小功能，驗證註冊意願。正式版會加入白標報告與授權方案。")
    with st.form("adv_signup"):
        name = st.text_input("姓名 / 公司名")
        email = st.text_input("Email")
        phone = st.text_input("手機")
        brand = st.text_input("希望顯示於報告的顧問品牌名稱")
        if st.form_submit_button("建立帳號（示意）"):
            st.success("註冊成功（示意）。正式版將儲存資料並寄出歡迎信。")

    # Footer
    footer()

def page_plans():
    st.title("授權與高階會員方案（合規）")
    c1, c2 = st.columns(2)
    with c1:
        st.header("Starter（授權）")
        st.markdown(
            "- AI 診斷、提案草案、案例庫（基礎）  \n"
            "- 簡版報告（白標）  \n"
            "- 客戶個案版本歷程  \n"
            "- **NT$ 3,600 / 月** 或 **NT$ 36,000 / 年**"
        )
    with c2:
        st.header("Pro（高階會員）")
        st.markdown(
            "- 進階策略模組與圖像化報告客製  \n"
            "- 專屬培訓與話術庫、實戰案例包  \n"
            "- 專案協作席次 3 位（團隊版）  \n"
            "- **NT$ 12,000 / 月** 或 **NT$ 120,000 / 年**"
        )
    st.caption("合規：平台僅收授權與專業服務費，不參與佣金分配或分潤。")

    # Footer
    footer()

def pa
