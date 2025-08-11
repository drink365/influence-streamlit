# utils.py
# 統一放常數與計算函式，供多頁面共用

from math import inf

class TaxConstants:
    # 遺產稅級距（元）
    ESTATE_TAX_THRESHOLDS = [
        (50_000_000, 0.10),
        (100_000_000, 0.15),
        (200_000_000, 0.20),
        (400_000_000, 0.30),
        (inf, 0.40),
    ]
    # 免稅額（元）
    BASIC_DEDUCTION   = 13_200_000    # 基本免稅額
    SPOUSE_DEDUCTION  = 49_300_000    # 配偶
    DEPENDENT_DEDUCTION = 4_930_000   # 受扶養親屬（每人）

    # 贈與稅
    GIFT_ANNUAL_EXEMPTION = 2_440_000
    GIFT_THRESHOLDS = [
        (25_000_000, 0.10),
        (50_000_000, 0.15),
        (inf,        0.20),
    ]


def _progressive_tax(taxable: float, brackets: list[tuple[float, float]]) -> float:
    """依累進級距計算稅額。brackets: [(上限, 稅率), ...]"""
    if taxable <= 0:
        return 0.0
    tax = 0.0
    last = 0.0
    for limit, rate in brackets:
        if taxable > limit:
            tax += (limit - last) * rate
            last = limit
        else:
            tax += (taxable - last) * rate
            break
    return max(0.0, tax)


def calculate_estate_tax(taxable_base: float, spouse_count: int = 0, dependent_count: int = 0) -> float:
    """
    遺產稅簡化版估算：
    - 課稅基礎 = 淨遺產 - （基本 + 配偶*1 + 受扶養*每人）
    - 稅率：10%/15%/20%/30%/40%（依級距）
    回傳單位：元
    """
    deductions = (
        TaxConstants.BASIC_DEDUCTION
        + (TaxConstants.SPOUSE_DEDUCTION if spouse_count >= 1 else 0)
        + (TaxConstants.DEPENDENT_DEDUCTION * max(0, int(dependent_count)))
    )
    taxable = max(0.0, float(taxable_base) - float(deductions))
    return _progressive_tax(taxable, TaxConstants.ESTATE_TAX_THRESHOLDS)


def calculate_gift_tax(amount: float) -> float:
    """
    贈與稅簡化版估算（年免稅額 244 萬，稅率 10%/15%/20% 級距）
    回傳單位：元
    """
    taxable = max(0.0, float(amount) - TaxConstants.GIFT_ANNUAL_EXEMPTION)
    return _progressive_tax(taxable, TaxConstants.GIFT_THRESHOLDS)


def format_wan(amount: float, decimals: int = 1) -> str:
    """將金額（元）轉成『萬元』字串，預設保留 1 位小數。"""
    fmt = f"{{:,.{decimals}f}} 萬元"
    return fmt.format(float(amount) / 10_000.0)
