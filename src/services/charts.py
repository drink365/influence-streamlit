from __future__ import annotations
from typing import List, Tuple
import math
import matplotlib.pyplot as plt
from matplotlib.sankey import Sankey

from src.domain.tax_rules import TaxConstants

# --- 既有：各級距稅額 Bar ---
def _compute_tax_components_wan(taxable_base_wan: float, brackets: List[Tuple[float, float]]) -> List[Tuple[str, float]]:
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
    c = constants or TaxConstants()
    parts = _compute_tax_components_wan(taxable_base_wan, list(c.TAX_BRACKETS))
    labels = [p[0] for p in parts]
    values = [p[1] for p in parts]

    fig, ax = plt.subplots(figsize=(6, 3.6))
    ax.bar(labels, values)
    ax.set_title("各級距稅額拆解（萬元）")
    ax.set_xlabel("級距")
    ax.set_ylabel("稅額（萬）")
    for i, v in enumerate(values):
        ax.text(i, v, f"{v:,.1f}", ha="center", va="bottom", fontsize=9)
    fig.tight_layout()
    return fig

# --- 新增：節稅對比（實際上是「稅後資金缺口」對比） ---

def savings_compare_bar(current_tax_yuan: float, coverage_yuan: float):
    """
    畫兩根 Bar：
      - 稅額（元）
      - 稅後資金缺口（= max(稅額 - 保單/信託預留, 0)）
    目的：傳達「方案降低稅後現金壓力」，避免不當宣稱減稅。
    """
    current_tax = max(float(current_tax_yuan), 0.0)
    coverage = max(float(coverage_yuan), 0.0)
    gap = max(current_tax - coverage, 0.0)

    fig, ax = plt.subplots(figsize=(6, 3.6))
    labels = ["稅額", "稅後資金缺口"]
    values = [current_tax, gap]
    ax.bar(labels, values)
    ax.set_title("方案對比：稅後資金缺口")
    ax.set_ylabel("金額（元）")
    for i, v in enumerate(values):
        ax.text(i, v, f"{v:,.0f}", ha="center", va="bottom", fontsize=9)
    fig.tight_layout()
    return fig

# --- 新增：簡化 Sankey（資產→稅款/家族；顯示保單覆蓋） ---

def simple_sankey(total_assets_yuan: float, tax_yuan: float, reserve_yuan: float):
    """
    節點：
      資產 → 稅款、家族；另以「保單預留」覆蓋部分稅款（視覺上作為稅款的分流來源）。
    說明：matplotlib.sankey 限制較多，這裡做簡化視覺，不求完美精細。
    """
    total = max(float(total_assets_yuan), 0.0)
    tax = max(float(tax_yuan), 0.0)
    reserve = max(float(reserve_yuan), 0.0)
    reserve_to_tax = min(reserve, tax)
    other_tax = tax - reserve_to_tax
    to_family = max(total - tax, 0.0)

    # 為避免 0 造成不可視，給極小值
    eps = max(total * 1e-6, 1.0)

    fig = plt.figure(figsize=(7.2, 3.8))
    ax = fig.add_subplot(1, 1, 1, xticks=[], yticks=[])
    ax.set_title("資金流示意（資產→稅款/家族；保單覆蓋稅款）")

    # 第一條 Sankey：資產流出到 稅款(其他負擔) 與 家族
    sankey = Sankey(ax=ax, format='%.0f')
    flows1 = [total, -other_tax if other_tax > 0 else -eps, -to_family if to_family > 0 else -eps]
    labels1 = ["資產總額", "稅款（其他資金）", "留給家族"]
    orientations1 = [0, 1, -1]
    sankey.add(flows=flows1, labels=labels1, orientations=orientations1, trunklength=1.0, pathlengths=[0.4,0.4,0.4])

    # 第二條 Sankey：保單預留 → 稅款（與第一條的稅款端相接）
    if reserve_to_tax > 0:
        sankey.add(flows=[reserve_to_tax, -reserve_to_tax], labels=["保單預留", "稅款（保單覆蓋）"], orientations=[0, 0], prior=0, connect=(0, 1), pathlengths=[0.4,0.3])

    sankey.finish()
    fig.tight_layout()
    return fig
