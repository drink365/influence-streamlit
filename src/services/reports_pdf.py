from __future__ import annotations
from pathlib import Path
from typing import Dict, Any
from datetime import datetime

from src.services.report_templates import render_template, fig_to_data_uri
from src.services.charts import tax_breakdown_bar, asset_pie
from src.domain.tax_loader import load_tax_constants

OUT_DIR = Path("data/reports")
OUT_DIR.mkdir(parents=True, exist_ok=True)

def _html_to_pdf(html: str, out_path: Path) -> bool:
    """優先使用 WeasyPrint；若環境無套件則回傳 False。"""
    try:
        from weasyprint import HTML  # type: ignore
        HTML(string=html).write_pdf(out_path.as_posix())
        return True
    except Exception:
        return False

def build_pdf_report(case: Dict[str, Any]) -> Path:
    """產生完整版 PDF 報告（或退回 HTML）。回傳實際輸出的檔案路徑。"""
    # 準備數據
    case_id = case["id"]
    client_alias = case.get("client_alias", "")
    net_estate = float(case.get("net_estate", 0))
    tax_estimate = float(case.get("tax_estimate", 0))
    liquidity_needed = float(case.get("liquidity_needed", 0))

    # 讀 payload
    import json
    payload = {}
    try:
        payload = json.loads(case.get("payload_json") or case.get("plan_json") or "{}")
    except Exception:
        payload = {}

    # 取課稅基礎（萬）與資產分布
    taxable_base_wan = float(payload.get("taxable_base_wan", 0) or 0)
    assets_fin = float(case.get("assets_financial", 0))
    assets_re  = float(case.get("assets_realestate", 0))
    assets_biz = float(case.get("assets_business", 0))

    # 生成圖像（轉成 data URI 讓 HTML 直接嵌入）
    constants = load_tax_constants()
    fig1 = tax_breakdown_bar(taxable_base_wan, constants=constants)
    fig2 = asset_pie(assets_fin, assets_re, assets_biz)
    img_tax = fig_to_data_uri(fig1)
    img_asset = fig_to_data_uri(fig2)

    # 模板上下文
    context = {
        "title": "傳承診斷報告",
        "case_id": case_id,
        "client_alias": client_alias,
        "date_str": datetime.now().strftime("%Y-%m-%d"),
        "net_estate": f"{net_estate:,.0f}",
        "tax_estimate": f"{tax_estimate:,.0f}",
        "liquidity_needed": f"{liquidity_needed:,.0f}",
        "rules_version": payload.get("rules_version", ""),
        "taxable_base_wan": f"{taxable_base_wan:,.0f}",
        "img_tax": img_tax,
        "img_asset": img_asset,
        "notes": [
            "本報告僅供參考；完整規劃須由專業顧問審閱。",
            "圖表與稅則基於當前版本設定，未含未來法令變動風險。",
        ],
    }

    html = render_template("report_full.html", context)

    # 優先輸出 PDF；失敗則保留 HTML
    out_pdf = OUT_DIR / f"{case_id}_report_full.pdf"
    out_html = OUT_DIR / f"{case_id}_report_full.html"
    success = _html_to_pdf(html, out_pdf)
    if success:
        return out_pdf
    out_html.write_text(html, encoding="utf-8")
    return out_html
