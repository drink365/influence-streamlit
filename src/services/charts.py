# src/services/charts.py
from __future__ import annotations
from typing import List, Tuple, Dict
import math

import matplotlib.pyplot as plt

from src.domain.tax_rules import TaxConstants

def _compute_tax_components_wan(taxable_base_wan: float, brackets: List[Tuple[float, float]]) -> List[Tuple[str, float]]:
    """
    將課稅基礎（萬）依級距拆成各級稅額（萬）。
    brackets: [(上限_萬, 稅率), ...]；最後一級上限應為 inf
    回傳: [(label, tax_wan), ...]
    """
    parts = []
    prev = 0.0
    for idx, (upper, rate) in enumerate(brackets, start=1):
        if taxable_base_wan <= prev:
            parts.append((f"L{idx}", 0.0))
            continue
        chunk = min(taxable_base_wan, upper) - prev
        tax_wan = max(chunk, 0.0) * rate
        parts.append((f"L{idx}", tax_wan))
        prev = upper
        if math.isinf(upper):
            break
    return parts

def tax_breakdown_bar(taxable_base_wan: float, *, constants: TaxConstants | None = None):
    """
    依當前 TaxConstants 將稅額拆解並畫 Bar 圖（單位：萬元）。
    回傳: matplotlib Figure
    """
    c = constants or TaxConstants()
    parts = _compute_tax_components_wan(taxable_base_wan, list(c.TAX_BRACKETS))
    labels = [p[0] for p in parts]
    values = [p[1] for p in parts]

    fig, ax = plt.subplots(figsize=(6, 3.6))  # 單張圖，避免子圖
    ax.bar(labels, values)  # 不指定顏色，遵循基礎樣式
    ax.set_title("各級距稅額拆解（萬元）")
    ax.set_xlabel("級距")
    ax.set_ylabel("稅額（萬）")
    for i, v in enumerate(values):
        ax.text(i, v, f"{v:,.1f}", ha="center", va="bottom", fontsize=9)
    fig.tight_layout()
    return fig

def asset_pie(financial: float, realestate: float, business: float):
    """
    資產結構圓餅圖（輸入：元）。內部自動換算成佔比顯示。
    回傳: matplotlib Figure
    """
    vals = [max(financial, 0.0), max(realestate, 0.0), max(business, 0.0)]
    labels = ["金融資產", "不動產", "公司股權"]
    total = sum(vals)
    if total <= 0:
        # 避免 0 除，給一張空心圖
        vals = [1, 1, 1]
        labels = ["金融資產(空)", "不動產(空)", "公司股權(空)"]

    fig, ax = plt.subplots(figsize=(6, 3.6))
    wedges, _ = ax.pie(vals, labels=None, autopct=None, startangle=90)
    ax.set_title("資產結構（佔比）")
    # 自己標上百分比
    if total > 0:
        pct = [v / total * 100 for v in vals]
        legend_labels = [f"{l}  {p:,.1f}%" for l, p in zip(labels, pct)]
    else:
        legend_labels = labels
    ax.legend(wedges, legend_labels, loc="center left", bbox_to_anchor=(1, 0.5))
    fig.tight_layout()
    return fig
