# pages/2_Diagnostic.py
import streamlit as st
from pathlib import Path
from datetime import datetime
from zoneinfo import ZoneInfo

from src.ui.footer import footer
from src.ui.theme import inject_css
from src.repos.cases import CaseRepo
from src.config import DATA_DIR

# ---------------- 基本設定 / 風格 ----------------
st.set_page_config(page_title="60 秒快速診斷", page_icon="🧭", layout="wide")
inject_css()

PRIMARY = "#BD0E1B"   # 與首頁/預約一致
ACCENT  = "#A88716"
INK     = "#3C3F46"
BG_SOFT = "#F7F7F8"

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
  .yc-step {{
    display:flex; gap:10px; align-items:center; margin:.4rem 0 1rem;
  }}
  .yc-step .dot {{
    width:24px; height:24px; border-radius:999px; line-height:24px; text-align:center;
    font-weight:700; color:#fff; background:{PRIMARY};
  }}
  .yc-step .label {{ color:#333; font-weight:600; }}
  .yc-cta button[kind="primary"] {{
    background:{PRIMARY} !important; border-color:{PRIMARY} !important;
    border-radius: 999px !important; font-weight: 700 !important;
  }}
  .yc-muted {{ color:#666; font-size:13px; }}
</style>
""", unsafe_allow_html=True)

# ---------------- 資料層保險：確保 data 目錄存在 ----------------
try:
    Path(DATA_DIR).mkdir(parents=True, exist_ok=True)
except Exception as e:
    st.error(f"無法建立資料夾 data/：{e}")

repo = CaseRepo()
TPE = ZoneInfo("Asia/Taipei")

# ---------------- Hero + 流程提示 ----------------
st.markdown('<div class="yc-hero">', unsafe_allow_html=True)
st.markdown('<span class="yc-badge">快速診斷</span>', unsafe_allow_html=True)
st.markdown("<h1>60 秒快速診斷</h1>", unsafe_allow_html=True)
st.markdown("<p>填寫關鍵資訊，立即產出初步風險重點、建議所需流動性與保障缺口。</p>", unsafe_allow_html=True)
st.markdown("</div>", unsafe_allow_html=True)

st.markdown("<div class='yc-step'><div class='dot'>1</div><div class='label'>填寫資訊</div></div>", unsafe_allow_html=True)

# ---------------- 表單（單一 st.form，避免 st.button 與 form 衝突） ----------------
with st.form("diag_form", clear_on_submit=False):
    st.markdown('<div class="yc-card">', unsafe_allow_html=True)
    st.write("### 聯絡方式（必填）")
    c1, c2 = st.columns(2)
    with c1:
        name  = st.text_input("姓名 *", placeholder="請輸入姓名")
        email = st.text_input("Email *", placeholder="name@example.com")
    with c2:
        mobile = st.text_input("手機 *", placeholder="+886 9xx xxx xxx")
        marital = st.selectbox("婚姻狀況 *", ["未婚", "已婚", "離婚", "鰥/寡"])

    st.markdown("</div>", unsafe_allow_html=True)

    st.markdown('<div class="yc-card">', unsafe_allow_html=True)
    st.write("### 家庭概況（必填）")
    c3, c4, c5 = st.columns(3)
    with c3:
        children = st.number_input("子女人數 *", min_value=0, max_value=10, value=0, step=1)
    with c4:
        heirs_involved = st.selectbox("是否已有繼承人參與討論？ *", ["尚未", "部份", "已全面參與"])
    with c5:
        governance = st.selectbox("是否有家族會議/章程？ *", ["尚未", "初步討論", "已建立"])

    st.markdown("</div>", unsafe_allow_html=True)

    st.markdown('<div class="yc-card">', unsafe_allow_html=True)
    st.write("### 資產盤點（金額請填「萬元」）")
    a1, a2, a3, a4 = st.columns(4)
    with a1:
        equity = st.number_input("公司股權（萬元）*", min_value=0.0, step=10.0, value=0.0)
    with a2:
        real_estate = st.number_input("不動產（萬元）*", min_value=0.0, step=10.0, value=0.0)
    with a3:
        financial = st.number_input("金融資產（萬元）*", min_value=0.0, step=10.0, value=0.0)
    with a4:
        insurance_cov = st.number_input("既有保單保額（萬元）*", min_value=0.0, step=10.0, value=0.0)

    total_assets = equity + real_estate + financial

    st.markdown("</div>", unsafe_allow_html=True)

    st.markdown('<div class="yc-card">', unsafe_allow_html=True)
    st.write("### 重點關注（多選）")
    focus = st.multiselect(
        "請選擇您最在意的議題",
        ["節稅效率", "現金流穩定", "交棒安排", "資產保全", "家族治理", "慈善與影響力"],
        default=["節稅效率","現金流穩定"]
    )
    st.caption("提示：選擇 2–3 項即可，我們後續會依優先順序設計方案。")
    st.markdown("</div>", unsafe_allow_html=True)

    st.markdown("<div class='yc-step'><div class='dot'>2</div><div class='label'>檢查與送出</div></div>", unsafe_allow_html=True)
    st.markdown('<div class="yc-card">', unsafe_allow_html=True)
    st.caption("送出前請再次確認：所有「*」欄位皆為必填，數字不得為負。")
    submit = st.form_submit_button("產出診斷結果 ➜", type="primary", use_container_width=True)
    st.markdown("</div>", unsafe_allow_html=True)

# ---------------- 送出後處理 ----------------
if submit:
    # 1) 必填檢查
    missing = []
    if not name.strip():   missing.append("姓名")
    if not email.strip():  missing.append("Email")
    if not mobile.strip(): missing.append("手機")

    if missing:
        st.error("請填寫必填欄位： " + "、".join(missing))
    elif any(x < 0 for x in [equity, real_estate, financial, insurance_cov]):
        st.error("資產金額不可為負數，請重新檢查。")
    else:
        # 2) 簡易試算（示意）：建議所需流動性與保障缺口
        #    - 目標流動性 = 10% × （股權 + 不動產 + 金融）
        #    - 保障缺口   = max(0, 目標流動性 - 既有保額)
        target_liquidity = round(total_assets * 0.10, 2)
        protection_gap = max(0.0, round(target_liquidity - insurance_cov, 2))

        ts_local = datetime.now(TPE).strftime("%Y-%m-%d %H:%M:%S %Z")

        # 3) 寫入個案（CSV）
        try:
            case = {
                "ts": ts_local,                 # 直接存台北時間字串
                "case_id": "",                  # 讓 repo 填（若你的實作會自動生成）
                "name": name.strip(),
                "email": email.strip(),
                "mobile": mobile.strip(),
                "marital": marital,
                "children": int(children),
                "equity": float(equity),
                "real_estate": float(real_estate),
                "financial": float(financial),
                "insurance_cov": float(insurance_cov),
                "total_assets": float(total_assets),
                "focus": ";".join(focus),
                # 試算欄位（結果頁可直接使用）
                "target_liquidity": float(target_liquidity),
                "protection_gap": float(protection_gap),
                "heirs_involved": heirs_involved,
                "governance": governance,
            }
            saved = repo.add(case)  # 預期回傳含 case_id 的 dict；若無，下面做容錯
            case_id = (saved.get("case_id") if isinstance(saved, dict) else None) or \
                      getattr(saved, "get", lambda *_: None)("case_id") or \
                      getattr(saved, "case_id", None) or \
                      "CASE"

            # 4) 狀態保存 & 導向
            st.session_state["last_case_id"] = case_id
            st.session_state["diag_result"] = {
                "case_id": case_id,
                "target_liquidity": target_liquidity,
                "protection_gap": protection_gap,
                "total_assets": total_assets,
                "focus": focus,
            }

            # 友善提示 + 進入結果頁
            st.success(f"已建立個案：{case_id}，正在產出結果…")
            st.markdown("<div class='yc-step'><div class='dot'>3</div><div class='label'>檢視結果</div></div>", unsafe_allow_html=True)
            st.rerun()  # 讓外層 router 讀到最新 session_state

        except Exception as e:
            st.error(f"寫入個案資料時發生錯誤：{e}")

# ---------------- 使用提示（若尚未送出） ----------------
if not submit:
    st.markdown("<div class='yc-step'><div class='dot'>3</div><div class='label'>檢視結果</div></div>", unsafe_allow_html=True)
    with st.container():
        st.markdown(
            """
            <div class="yc-card">
              <b>送出後會自動跳轉至「結果」頁</b>，並提供：
              <ul>
                <li>風險重點與建議所需流動性</li>
                <li>保障缺口（以目前保障與目標流動性差額計算）</li>
                <li>依您勾選的關注議題產出「下一步行動清單」</li>
              </ul>
              <div class="yc-muted">註：此為初步診斷，完整方案仍需結合法律／稅務／公司治理等專業評估。</div>
            </div>
            """,
            unsafe_allow_html=True
        )

footer()
