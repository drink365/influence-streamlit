# pages/2_Diagnostic.py
# 遺產稅診斷（單位：萬元）— 計算後可建立案件並跳到結果頁（用 goto）

import uuid
from datetime import datetime
from math import inf
import streamlit as st
from src.utils.nav import goto

st.set_page_config(page_title="遺產稅診斷", page_icon="💡", layout="wide")
st.title("📊 遺產稅診斷（單位：萬元）")
st.caption("依正式規則計算：免稅額、喪葬費、配偶與各類受扶養扣除皆已內建；級距為 10% / 15% / 20%。")

# 正式規則（萬）
EXEMPT_AMOUNT = 1333.0
FUNERAL_EXPENSE = 138.0
SPOUSE_DEDUCTION_VALUE = 553.0
ADULT_CHILD_DEDUCTION = 56.0
PARENTS_DEDUCTION = 138.0
DISABLED_DEDUCTION = 693.0
OTHER_DEPENDENTS_DEDUCTION = 56.0
TAX_BRACKETS = [(5621.0, 0.10), (11242.0, 0.15), (inf, 0.20)]
WAN = 10_000

def fmt_wan(x: float) -> str:
    return f"{float(x):,.1f} 萬元"

def compute_total_deductions_wan(has_spouse: bool, adult_children: int, parents: int,
                                 disabled_people: int, other_dependents: int) -> float:
    dep_total = (max(0,int(adult_children))*ADULT_CHILD_DEDUCTION
                 + max(0,int(parents))*PARENTS_DEDUCTION
                 + max(0,int(disabled_people))*DISABLED_DEDUCTION
                 + max(0,int(other_dependents))*OTHER_DEPENDENTS_DEDUCTION)
    return float(FUNERAL_EXPENSE + (SPOUSE_DEDUCTION_VALUE if has_spouse else 0.0) + dep_total)

def progressive_tax_wan(taxable_base_wan: float) -> float:
    if taxable_base_wan <= 0: return 0.0
    tax, last = 0.0, 0.0
    for limit, rate in TAX_BRACKETS:
        if limit == inf or taxable_base_wan <= limit:
            tax += (taxable_base_wan - last) * rate; break
        tax += (limit - last) * rate; last = limit
    return max(0.0, tax)

with st.form("estate_form"):
    a1, a2 = st.columns(2)
    with a1:
        total_assets_wan = st.number_input("總資產（萬元）", min_value=0.0, step=10.0, value=10_000.0, format="%.1f")
    with a2:
        total_liabilities_wan = st.number_input("總負債（萬元）", min_value=0.0, step=10.0, value=0.0, format="%.1f")
    st.divider()
    b1, b2, b3, b4, b5 = st.columns(5)
    with b1: has_spouse = st.checkbox("有配偶", value=True)
    with b2: adult_children = st.number_input("成年子女（人）", min_value=0, step=1, value=2)
    with b3: parents = st.number_input("直系尊親屬（人）", min_value=0, step=1, value=0)
    with b4: disabled_people = st.number_input("重度身心障礙（人）", min_value=0, step=1, value=0)
    with b5: other_dependents = st.number_input("其他受扶養（人）", min_value=0, step=1, value=0)
    submitted = st.form_submit_button("開始計算")

if submitted:
    net_estate_wan = max(0.0, float(total_assets_wan) - float(total_liabilities_wan))
    total_deductions_wan = compute_total_deductions_wan(bool(has_spouse), int(adult_children),
                                                        int(parents), int(disabled_people), int(other_dependents))
    taxable_base_wan = max(0.0, net_estate_wan - EXEMPT_AMOUNT - total_deductions_wan)
    tax_wan = progressive_tax_wan(taxable_base_wan)

    st.subheader("計算結果（單位：萬元）")
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("淨遺產", fmt_wan(net_estate_wan))
    c2.metric("合計扣除額", fmt_wan(total_deductions_wan))
    c3.metric("課稅基礎", fmt_wan(taxable_base_wan))
    c4.metric("估算遺產稅", fmt_wan(tax_wan))

    st.markdown("---")
    st.subheader("下一步")
    st.caption("按下按鈕後，會建立案件並前往結果頁（可下載報告、建立分享連結、回報成交）。")

    from src.repos.case_repo import CaseRepo
    try:
        from src.services.safe_event import log_safe
    except Exception:
        def log_safe(*a, **k): pass

    def _wan_to_yuan(x: float) -> float: return float(x) * WAN

    case_payload = {
        "id": uuid.uuid4().hex[:8].upper(),
        "advisor_id": st.session_state.get("advisor_id", "guest"),
        "advisor_name": st.session_state.get("advisor_name", "未登入"),
        "client_alias": "未命名",
        "assets_financial": 0.0,
        "assets_realestate": 0.0,
        "assets_business": 0.0,
        "liabilities": _wan_to_yuan(total_liabilities_wan),
        "net_estate": _wan_to_yuan(net_estate_wan),
        "tax_estimate": _wan_to_yuan(tax_wan),
        "liquidity_needed": _wan_to_yuan(tax_wan),
        "status": "Prospect",
        "payload_json": None,
        "created_at": datetime.utcnow().isoformat(),
        "updated_at": datetime.utcnow().isoformat(),
    }

    if st.button("✅ 建立案件並前往結果頁", use_container_width=True):
        try:
            if hasattr(CaseRepo, "upsert"): CaseRepo.upsert(case_payload)
            else: CaseRepo.create(case_payload)
            try:
                log_safe(case_payload["id"], "CASE_CREATED", {
                    "source": "Diagnostic",
                    "net_estate_wan": float(net_estate_wan),
                    "tax_wan": float(tax_wan),
                })
            except Exception:
                pass
            # 帶上 case_id 再跳
            try: st.query_params.update({"case_id": case_payload["id"]})
            except Exception: pass
            goto(st, "pages/3_Result.py")
        except Exception as e:
            st.error(f"建立案件失敗：{e}")
