from __future__ import annotations
from dataclasses import dataclass
from typing import List, Dict, Any

"""
稅則模組（對齊 estate-tax-app）
- 內部採用「萬元」計算，對外 API 使用「元」輸入/輸出
- 參數含：免稅額、喪葬費、配偶/子女/父母/重障/其他受扶養扣除
- 累進級距：[(上限_萬, 稅率), ...]，最後一級上限用 float('inf')
"""

@dataclass
class TaxConstants:
    UNIT_FACTOR: float = 10000.0  # 1 萬元 = 10,000 元
    # 免稅與扣除（單位：萬）
    EXEMPT_AMOUNT: float = 1333.0
    FUNERAL_EXPENSE: float = 138.0
    SPOUSE_DEDUCTION_VALUE: float = 553.0
    ADULT_CHILD_DEDUCTION: float = 56.0
    PARENTS_DEDUCTION: float = 138.0
    DISABLED_DEDUCTION: float = 693.0
    OTHER_DEPENDENTS_DEDUCTION: float = 56.0
    # 累進級距（上限：萬；稅率：0~1）
    TAX_BRACKETS: List[tuple] = (
        (5621.0, 0.10),
        (11242.0, 0.15),
        (float("inf"), 0.20),
    )
    # 建議稅源緩衝倍數（例如 1.1）
    BUFFER_MULTIPLIER: float = 1.10
    VERSION: str = "estate-tax-app-v1"


class EstateTaxCalculator:
    def __init__(self, constants: TaxConstants | None = None):
        self.c = constants or TaxConstants()

    # ===== 內部計算都用「萬」 =====
    def _yuan_to_wan(self, amount_yuan: float) -> float:
        return float(amount_yuan) / self.c.UNIT_FACTOR

    def _wan_to_yuan(self, amount_wan: float) -> float:
        return float(amount_wan) * self.c.UNIT_FACTOR

    def compute_total_deductions_wan(
        self,
        has_spouse: bool,
        adult_children: int,
        parents: int,
        disabled_people: int,
        other_dependents: int,
    ) -> float:
        return (
            (self.c.SPOUSE_DEDUCTION_VALUE if has_spouse else 0.0)
            + self.c.FUNERAL_EXPENSE
            + adult_children * self.c.ADULT_CHILD_DEDUCTION
            + parents * self.c.PARENTS_DEDUCTION
            + disabled_people * self.c.DISABLED_DEDUCTION
            + other_dependents * self.c.OTHER_DEPENDENTS_DEDUCTION
        )

    def compute_taxable_base_wan(
        self,
        net_estate_wan: float,
        total_deductions_wan: float,
    ) -> float:
        # 課稅基礎 = 淨遺產 - 免稅額 - 扣除額
        return max(net_estate_wan - self.c.EXEMPT_AMOUNT - total_deductions_wan, 0.0)

    def progressive_tax_wan(self, taxable_base_wan: float) -> float:
        tax = 0.0
        prev = 0.0
        for upper, rate in self.c.TAX_BRACKETS:
            if taxable_base_wan <= prev:
                break
            chunk = min(taxable_base_wan, upper) - prev
            tax += chunk * rate
            prev = upper
        return max(tax, 0.0)

    # ===== 對外 API：輸入/輸出均為「元」 =====
    def diagnose_yuan(
        self,
        net_estate_yuan: float,
        *,
        has_spouse: bool,
        adult_children: int,
        parents: int,
        disabled_people: int,
        other_dependents: int,
        buffer_multiplier: float | None = None,
    ) -> Dict[str, Any]:
        # 轉萬
        net_wan = self._yuan_to_wan(net_estate_yuan)
        # 扣除（萬）
        deductions_wan = self.compute_total_deductions_wan(
            has_spouse, adult_children, parents, disabled_people, other_dependents
        )
        # 課稅基礎（萬）
        base_wan = self.compute_taxable_base_wan(net_wan, deductions_wan)
        # 稅額（萬）
        tax_wan = self.progressive_tax_wan(base_wan)
        # 換回元
        tax_yuan = self._wan_to_yuan(tax_wan)
        buf = float(buffer_multiplier or self.c.BUFFER_MULTIPLIER)
        liquidity_needed_yuan = round(tax_yuan * buf)
        return {
            "rules_version": self.c.VERSION,
            "unit_factor": self.c.UNIT_FACTOR,
            "exempt_amount_wan": self.c.EXEMPT_AMOUNT,
            "deductions_wan": deductions_wan,
            "taxable_base_wan": base_wan,
            "tax_yuan": tax_yuan,
            "recommended_liquidity_yuan": liquidity_needed_yuan,
            "buffer_multiplier": buf,
            "inputs": {
                "has_spouse": has_spouse,
                "adult_children": adult_children,
                "parents": parents,
                "disabled_people": disabled_people,
                "other_dependents": other_dependents,
            },
        }
