from __future__ import annotations
from typing import Dict, Any, List

"""
根據案件數據產出策略建議（規則型 MVP）：
- 以「降低稅後現金壓力」與「傳承合規與治理」為核心表述
- 不宣稱減稅；使用「預留稅源、資產隔離、受益人保障」等語彙
"""


def suggest(case: Dict[str, Any], payload: Dict[str, Any]) -> List[str]:
    tips: List[str] = []
    net = float(case.get("net_estate", 0))
    tax = float(case.get("tax_estimate", 0))
    need = float(case.get("liquidity_needed", 0))
    params = (payload.get("params") or {}) if isinstance(payload, dict) else {}

    # 1) 稅後現金壓力
    ratio = (tax / net) if net > 0 else 0
    if tax > 0:
        if ratio >= 0.15:
            tips.append("建立以保單為核心的『稅源預留池』：預計覆蓋稅額的 100%–120%，避免資產拋售造成折價與時程壓力。")
        else:
            tips.append("規劃稅源預留池覆蓋主要稅額（80%–100%），將現金壓力移轉至預留工具。")

    # 2) 家庭結構
    if bool(params.get("has_spouse")) and int(params.get("adult_children", 0)) >= 1:
        tips.append("設計『配偶＋子女』分層受益架構：近期現金流保障配偶、長期資產逐步移轉至下一代。")
    elif int(params.get("adult_children", 0)) >= 2:
        tips.append("多受益人情境：設定受益比例與監管機制，避免繼承爭議。")

    # 3) 資產結構
    fin = float(case.get("assets_financial", 0)); re = float(case.get("assets_realestate", 0)); biz = float(case.get("assets_business", 0))
    total = fin + re + biz
    if total > 0:
        if re / total >= 0.5:
            tips.append("不動產占比較高：建議以信託或保單預留支應稅款，降低短期變現風險。")
        if biz / total >= 0.3:
            tips.append("公司股權較高：建議同步規劃股東協議與家族治理章程，確保經營權穩定。")

    # 4) 法遵與文件
    tips.append("同步建置：遺囑、醫療意願/代理、保單受益人指定與信託條款，形成完整傳承文件組。")

    # 控制數量
    if len(tips) > 5:
        tips = tips[:5]
    return tips
