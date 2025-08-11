from __future__ import annotations
from pathlib import Path
from datetime import datetime
import io

# 延遲匯入：WeasyPrint 非必裝，裝不到就退回 HTML
try:
    from weasyprint import HTML
    HAS_WEASY = True
except Exception:
    HAS_WEASY = False

# 不在頂層匯入 charts，避免一出錯整檔無法 import
def _try_import_charts():
    try:
        # 相對匯入比絕對匯入更穩
        from .charts import (
            tax_breakdown_bar,
            asset_pie,
            savings_compare_bar,
            simple_sankey,
        )
        return {
            "tax_breakdown_bar": tax_breakdown_bar,
            "asset_pie": asset_pie,
            "savings_compare_bar": savings_compare_bar,
            "simple_sankey": simple_sankey,
        }, None
    except Exception as e:
        return None, e

def _ensure_outdir() -> Path:
    out = Path("data/reports")
    out.mkdir(parents=True, exist_ok=True)
    return out

def _png_bytes_from_fig(fig):
    """將 matplotlib 圖存成 PNG bytes"""
    import matplotlib.pyplot as plt
    buf = io.BytesIO()
    fig.savefig(buf, format="png", bbox_inches="tight", dpi=160)
    plt.close(fig)
    buf.seek(0)
    return buf.getvalue()

def _build_html(case: dict) -> str:
    """最簡 HTML 報告（即使沒有圖也能出）"""
    id_ = case.get("id", "")
    net = case.get("net_estate", 0.0)
    tax = case.get("tax_estimate", 0.0)
    liq = case.get("liquidity_needed", 0.0)

    return f"""
<!doctype html>
<html>
<head>
  <meta charset="utf-8"/>
  <title>規劃報告 - {id_}</title>
  <style>
    body {{ font-family: -apple-system, BlinkMacSystemFont, Segoe UI, Roboto, Noto Sans, Arial; margin: 32px; }}
    h1 {{ margin-bottom: 4px; }}
    .meta {{ color:#666; font-size: 12px; margin-bottom: 24px; }}
    .card {{ border:1px solid #eee; border-radius:12px; padding:16px; margin-bottom:12px; }}
    .kv {{ display:flex; gap:16px; }}
    .kv div {{ flex:1; }}
    .num {{ font-weight:600; font-size:20px; }}
  </style>
</head>
<body>
  <h1>規劃報告（簡版）</h1>
  <div class="meta">案件：{id_}｜產出時間：{datetime.now().strftime("%Y-%m-%d %H:%M")}</div>

  <div class="kv">
    <div class="card"><div>淨遺產</div><div class="num">{net:,.0f}</div></div>
    <div class="card"><div>估算稅額</div><div class="num">{tax:,.0f}</div></div>
    <div class="card"><div>建議預留稅源</div><div class="num">{liq:,.0f}</div></div>
  </div>

  <p style="margin-top:24px;color:#666;font-size:12px">
    本報告為教育性質示意，不構成保險或法律建議。
  </p>
</body>
</html>
"""

def build_pdf_report(case: dict) -> Path:
    """
    產生 PDF（若無 WeasyPrint 或圖表匯入失敗，會退回 HTML）。
    回傳檔案路徑（.pdf 或 .html）
    """
    outdir = _ensure_outdir()
    charts, charts_err = _try_import_charts()

    # 嘗試組圖（若失敗就不放圖）
    images = {}
    if charts:
        try:
            # 依現有欄位生成圖表（有多少用多少）
            if case.get("tax_estimate") and case.get("net_estate"):
                fig1 = charts["tax_breakdown_bar"](
                    float(case.get("tax_estimate")) / 10000.0  # 若此函式吃「萬」，自行調整
                )
                images["tax_breakdown.png"] = _png_bytes_from_fig(fig1)

            assets_fin = case.get("assets_financial") or 0.0
            assets_re  = case.get("assets_realestate") or 0.0
            assets_biz = case.get("assets_business") or 0.0
            if any([assets_fin, assets_re, assets_biz]):
                fig2 = charts["asset_pie"](assets_fin, assets_re, assets_biz)
                images["asset_pie.png"] = _png_bytes_from_fig(fig2)
        except Exception:
            # 圖表失敗就忽略，不要讓整個匯出掛掉
            images = {}

    # 基本 HTML
    html = _build_html(case)

    # 若能做成 PDF 就輸出 PDF；否則輸出 HTML
    case_id = case.get("id", "report")
    if HAS_WEASY:
        try:
            pdf_path = outdir / f"{case_id}.pdf"
            # 若要嵌入圖片，可在 HTML 中使用 data URI（此處為簡化版本，不嵌圖也能出）
            HTML(string=html).write_pdf(pdf_path.as_posix())
            return pdf_path
        except Exception:
            pass

    # 退回 HTML 檔
    html_path = outdir / f"{case_id}.html"
    html_path.write_text(html, encoding="utf-8")
    return html_path
