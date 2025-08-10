from docx import Document
from pathlib import Path

def generate_docx(case: dict, full: bool = False) -> str:
    doc = Document()
    doc.add_heading("傳承診斷報告", level=1)
    doc.add_paragraph(f"案件碼：{case['id']}")
    doc.add_paragraph(f"客戶：{case['client_alias']}")
    doc.add_paragraph(f"淨遺產：{case['net_estate']:,}")
    doc.add_paragraph(f"估算稅額：{case['tax_estimate']:,}")
    doc.add_paragraph(f"建議預留稅源：{case['liquidity_needed']:,}")

    if full:
        doc.add_heading("完整明細與建議", level=2)
        doc.add_paragraph("• 稅則假設與參數（示意，可替換為正式版）")
        doc.add_paragraph("• 資產分類明細與負債")
        doc.add_paragraph("• 策略建議：保險、信託、遺囑、公司治理架構、稅務安排（示意）")

    out_dir = Path("data/reports"); out_dir.mkdir(parents=True, exist_ok=True)
    fname = f"{case['id']}_report{'_full' if full else '_lite'}.docx"
    doc.save(out_dir / fname)
    return fname
