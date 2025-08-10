from __future__ import annotations
from pathlib import Path
from typing import Dict, Any
from datetime import datetime
import io, base64

from src.services.report_templates import render_template, fig_to_data_uri
from src.services.charts import tax_breakdown_bar, asset_pie
from src.domain.tax_loader import load_tax_constants
from src.services.brand import load_brand, logo_data_uri
from src.services.strategy_writer import suggest

OUT_DIR = Path("data/reports")
OUT_DIR.mkdir(parents=True, exist_ok=True)


def _html_to_pdf(html: str, out_path: Path) -> bool:
    try:
        from weasyprint import HTML  # type: ignore
        HTML(string=html).write_pdf(out_path.as_posix())
        return True
    except Exception:
        return False


def _qr_data_uri(url: str) -> str | None:
    """使用 qrcode（若無則回傳 None）。"""
    try:
        import qrcode  # type: ignore
        img = qrcode.make(url)
        buf = io.BytesIO()
        img.save(buf, format="PNG")
        b64 = base64.b64encode(buf.getvalue()).decode("ascii")
        return f"data:image/png;base64,{b64}"
    except Exception:
        return None


def build_pdf_report(case: Dict[str, Any]) -> Path:
    # ===== 基本數據 =====
    case_id = case["id"]
    client_alias = case.get("client_alias", "")
    net_estate = float(case.get("net_estate", 0))
    tax_estimate = float(case.get("tax_estimate", 0))
    liquidity_needed = float(case.get("liquidity_needed", 0))

    import json
    payload = {}
    try:
        payload = json.loads(case.get("payload_json") or case.get("plan_json") or "{}")
    except Exception:
        payload = {}

    taxable_base_wan = float(payload.get("taxable_base_wan", 0) or 0)
    assets_fin = float(case.get("assets_financial", 0))
    assets_re  = float(case.get("assets_realestate", 0))
    assets_biz = float(case.get("assets_business", 0))

    # ===== 圖像化 =====
    constants = load_tax_constants()
    fig1 = tax_breakdown_bar(taxable_base_wan, constants=constants)
    fig2 = asset_pie(assets_fin, assets_re, assets_biz)
    img_tax = fig_to_data_uri(fig1)
    img_asset = fig_to_data_uri(fig2)

    # ===== 品牌設定與聯絡 =====
    brand = load_brand()
    brand_logo = logo_data_uri(brand)
    contact = brand.get("contact", {})
    booking_url = contact.get("booking_url") or contact.get("website") or ""
    booking_qr = _qr_data_uri(booking_url) if booking_url else None

    # ===== 策略建議 =====
    strategies = suggest(case, payload)

    # ===== 模板上下文 =====
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
        # 品牌
        "brand_name": brand.get("name","永傳家族辦公室"),
        "primary_color": brand.get("primary_color"),
        "accent_color": brand.get("accent_color"),
        "text_color": brand.get("text_color"),
        "logo_data_uri": brand_logo,
        "contact": contact,
        # 策略
        "strategies": strategies,
        # QR
        "booking_qr": booking_qr,
    }

    html = render_template("report_full.html", context)

    out_pdf = OUT_DIR / f"{case_id}_report_full.pdf"
    out_html = OUT_DIR / f"{case_id}_report_full.html"
    if _html_to_pdf(html, out_pdf):
        return out_pdf
    out_html.write_text(html, encoding="utf-8")
    return out_html
