# pages/3_Result.py
# 穩健版 Result 頁：修正 charts 匯入錯誤、依賴失敗時自動退回、不讓整頁掛掉

import sys, pathlib, io
from datetime import datetime
import streamlit as st

# -----------------------------
# 路徑保險：確保可以 import src/*
# -----------------------------
ROOT = pathlib.Path(__file__).resolve().parents[1]  # 專案根目錄
if str(ROOT) not in sys.path:
    sys.path.append(str(ROOT))

# -----------------------------
# 依賴（延遲匯入與防呆）
# -----------------------------
_HAS_CHARTS = False
try:
    from src.services.charts import (
        tax_breakdown_bar,
        asset_pie,
        savings_compare_bar,
        simple_sankey,
    )
    _HAS_CHARTS = True
except Exception:
    # 圖表不可用時，提供 no-op 函式，避免頁面壞掉
    def _noop(*args, **kwargs):
        return None
    tax_breakdown_bar = asset_pie = savings_compare_bar = simple_sankey = _noop

# 報告輸出（PDF/HTML）
_HAS_REPORTS_PDF = False
try:
    from src.services.reports_pdf import build_pdf_report  # 會自動退回 HTML
    _HAS_REPORTS_PDF = True
except Exception:
    build_pdf_report = None

# 報告（HTML/DOCX 等其他）
_HAS_REPORTS = False
try:
    from src.services.reports import build_full_report_html  # 若有
    _HAS_REPORTS = True
except Exception:
    build_full_report_html = None

# Case 讀取
try:
    from src.repos.case_repo import CaseRepo
except Exception:
    CaseRepo = None

# 點數經濟（可選）
_HAS_BILLING = False
try:
    from src.services.billing import try_unlock_full_report, reward_won, balance
    _HAS_BILLING = True
except Exception:
    def try_unlock_full_report(*a, **k): return (True, "（未啟用扣點系統，本次視為已解鎖）")
    def reward_won(*a, **k): return None
    def balance(*a, **k): return 0

# -----------------------------
# 小工具
# -----------------------------
def _fmt_money(x: float) -> str:
    try:
        return f"{float(x):,.0f}"
    except Exception:
        return "—"

def _fmt_wan(x: float) -> str:
    try:
        return f"{float(x)/10_000:,.1f} 萬元"
    except Exception:
        return "—"

def _safe_pyplot(fig):
    if _HAS_CHARTS and fig is not None:
        st.pyplot(fig, use_container_width=True)

def _load_case(case_id: str | None):
    if CaseRepo is None:
        return None
    if case_id:
        row = CaseRepo.get(case_id)
        if row: return row
    # 沒指定 case_id 時，抓最新一筆
    try:
        rows = CaseRepo.list_latest(limit=1)
        return rows[0] if rows else None
    except Exception:
        return None

def _build_and_link_report(case: dict):
    """嘗試輸出 PDF；若不可用就退回 HTML。回傳 (path, label)"""
    if build_pdf_report:
        try:
            path = build_pdf_report(case)
            return str(path), "下載報告"
        except Exception:
            pass
    # 若 services.reports 有 HTML 產生器，就用它
    if build_full_report_html:
        try:
            html = build_full_report_html(case)
            out = pathlib.Path("data/reports"); out.mkdir(parents=True, exist_ok=True)
            p = out / f"{case.get('id','report')}.html"
            p.write_text(html, encoding="utf-8")
            return str(p), "下載報告（HTML）"
        except Exception:
            pass
    # 最簡 fallback：內建一個極簡 HTML
    out = pathlib.Path("data/reports"); out.mkdir(parents=True, exist_ok=True)
    p = out / f"{case.get('id','report')}.html"
    html = f"""<!doctype html><meta charset="utf-8">
    <h2>規劃報告（簡版）</h2>
    <div>案件：{case.get('id','')}</div>
    <div>產出時間：{datetime.now().strftime('%Y-%m-%d %H:%M')}</div>
    <ul>
      <li>淨遺產：{_fmt_money(case.get('net_estate',0))}</li>
      <li>估算稅額：{_fmt_money(case.get('tax_estimate',0))}</li>
      <li>建議預留稅源：{_fmt_money(case.get('liquidity_needed',0))}</li>
    </ul>
    <small>本報告為教育性質示意，不構成保險或法律建議。</small>
    """
    p.write_text(html, encoding="utf-8")
    return str(p), "下載報告（HTML）"

# -----------------------------
# UI
# -----------------------------
st.set_page_config(page_title="結果與報告", page_icon="📄", layout="wide")
st.title("📄 結果與報告")

# 參數：case_id（可從分享或前頁帶入）
q = st.query_params
case_id = q.get("case_id") if isinstance(q.get("case_id"), str) else (q.get("case_id")[0] if q.get("case_id") else "")
case = _load_case(case_id)

if not case:
    st.warning("尚未找到案件資料。請先完成診斷或從 Dashboard 選擇案件。")
    st.stop()

# 頂部資訊
st.caption(f"案件：{case.get('id','')}｜建立時間：{(case.get('created_at') or '')[:19].replace('T',' ')}")

# KPI
c1, c2, c3 = st.columns(3)
c1.metric("淨遺產（元）", _fmt_money(case.get("net_estate", 0.0)))
c2.metric("估算稅額（元）", _fmt_money(case.get("tax_estimate", 0.0)))
c3.metric("建議預留稅源（元）", _fmt_money(case.get("liquidity_needed", 0.0)))

st.divider()

# -----------------------------
# 解鎖區（管理碼 / 點數）
# -----------------------------
with st.expander("解鎖並下載完整報告", expanded=True):
    # 管理碼（不扣點）
    admin_key = st.secrets.get("ADMIN_KEY")
    ak = st.text_input("管理碼（內部測試用）", type="password", value="")
    admin_unlock = bool(admin_key) and ak and (ak == admin_key)

    # 點數解鎖（若安裝了 billing）
    user_id = st.session_state.get("advisor_id")  # 顧問登入後才會有
    cost_tip = st.secrets.get("CREDITS", {}).get("REPORT_FULL_COST", 5)
    unlocked_msg = None
    credit_unlock = False

    cols = st.columns(3)
    with cols[0]:
        if st.button("用管理碼解鎖", use_container_width=True):
            if admin_unlock:
                unlocked_msg = "管理碼驗證成功，已解鎖。"
            else:
                unlocked_msg = "管理碼錯誤或未設定。"

    with cols[1]:
        if _HAS_BILLING:
            if st.button(f"用點數解鎖（扣 {cost_tip} 點）", use_container_width=True, disabled=not user_id):
                ok, msg = try_unlock_full_report(user_id or "", case.get("id",""))
                credit_unlock = ok
                unlocked_msg = msg if msg else ("解鎖成功。" if ok else "解鎖失敗。")
        else:
            st.button("用點數解鎖（未啟用）", disabled=True, use_container_width=True)

    with cols[2]:
        if user_id and _HAS_BILLING:
            st.metric("我的點數", balance(user_id))

    if unlocked_msg:
        st.info(unlocked_msg)

    unlocked = admin_unlock or credit_unlock
    if unlocked:
        path, label = _build_and_link_report(case)
        st.success("已解鎖。您可以下載完整報告。")
        with open(path, "rb") as fh:
            st.download_button(label, data=fh.read(), file_name=pathlib.Path(path).name, mime="application/octet-stream")

st.divider()

# -----------------------------
# 視覺化（存在才畫，失敗不報錯）
# -----------------------------
left, right = st.columns(2)

with left:
    if _HAS_CHARTS:
        # 稅額結構（如果你的 charts 需要「萬」，這裡自行調整參數）
        tax = case.get("tax_estimate") or 0.0
        fig1 = tax_breakdown_bar(tax / 10_000.0)  # 給「萬」的版本；若你的函式吃「元」請改回 tax
        _safe_pyplot(fig1)
    else:
        st.info("圖表模組未載入，略過稅額圖。")

with right:
    if _HAS_CHARTS:
        fin = case.get("assets_financial") or 0.0
        re_ = case.get("assets_realestate") or 0.0
        biz = case.get("assets_business") or 0.0
        if any([fin, re_, biz]):
            fig2 = asset_pie(fin, re_, biz)
            _safe_pyplot(fig2)
    else:
        st.info("圖表模組未載入，略過資產配置圖。")

st.caption("＊本頁內容為教育性質示意，不構成保險或法律建議。")
