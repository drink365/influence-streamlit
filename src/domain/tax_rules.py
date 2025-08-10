# src/domain/tax_rules.py
from __future__ import annotations
from dataclasses import dataclass
from typing import List, Dict, Any

@dataclass
class TaxConstants:
    UNIT_FACTOR: float = 10000.0
    EXEMPT_AMOUNT: float = 1333.0
    FUNERAL_EXPENSE: float = 138.0
    SPOUSE_DEDUCTION_VALUE: float = 553.0
    ADULT_CHILD_DEDUCTION: float = 56.0
    PARENTS_DEDUCTION: float = 138.0
    DISABLED_DEDUCTION: float = 693.0
    OTHER_DEPENDENTS_DEDUCTION: float = 56.0
    TAX_BRACKETS: List[tuple] = (
        (5621.0, 0.10),
        (11242.0, 0.15),
        (float("inf"), 0.20),
    )
    BUFFER_MULTIPLIER: float = 1.10
    VERSION: str = "estate-tax-app-v1"

class EstateTaxCalculator:
    def __init__(self, constants: TaxConstants | None = None):
        self.c = constants or TaxConstants()

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
        return max(net_estate_wan - self.c.EXEMPT_AMOUNT - total_deductions_wan, 0.0)

    def progressive_tax_wan(self, taxable_base_wan: float) -> float:
        tax = 0.0
        prev_upper = 0.0
        for upper, rate in self.c.TAX_BRACKETS:
            if taxable_base_wan <= prev_upper:
                break
            chunk = min(taxable_base_wan, upper) - prev_upper
            tax += max(chunk, 0.0) * rate
            prev_upper = upper
        return max(tax, 0.0)

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
        net_wan = self._yuan_to_wan(net_estate_yuan)
        deductions_wan = self.compute_total_deductions_wan(
            has_spouse, adult_children, parents, disabled_people, other_dependents
        )
        base_wan = self.compute_taxable_base_wan(net_wan, deductions_wan)
        tax_wan = self.progressive_tax_wan(base_wan)
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
        }
