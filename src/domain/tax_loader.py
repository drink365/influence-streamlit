# src/domain/tax_loader.py
from __future__ import annotations
import json
from pathlib import Path
from datetime import date, datetime
from typing import Optional, Tuple, List

from src.domain.tax_rules import TaxConstants

CONFIG_PATH = Path("src/domain/tax_config.json")

def _parse_date(s: str) -> date:
    return datetime.strptime(s, "%Y-%m-%d").date()

def load_tax_constants(
    *,
    on_date: Optional[date] = None,
    version: Optional[str] = None,
    config_path: Path = CONFIG_PATH
) -> TaxConstants:
    """
    載入 JSON 設定，挑選最適用版本：
      - 若指定 version，直接取該版本
      - 否則用 on_date（預設 today）挑選 effective_from <= on_date 的最新版本
    回傳 TaxConstants（單位：萬）
    """
    on = on_date or date.today()
    data = json.loads(config_path.read_text(encoding="utf-8"))
    versions = data.get("versions", [])
    if not versions:
        raise RuntimeError("tax_config.json 缺少 versions")

    chosen = None
    if version:
        for v in versions:
            if v.get("version") == version:
                chosen = v
                break
        if not chosen:
            raise RuntimeError(f"找不到版本：{version}")
    else:
        # 選 effective_from <= on 的最新
        candidates = []
        for v in versions:
            eff = _parse_date(v.get("effective_from", "1900-01-01"))
            if eff <= on:
                candidates.append((eff, v))
        if not candidates:
            # 若沒有符合，就取最早一個
            chosen = sorted(versions, key=lambda x: x.get("effective_from", ""))[0]
        else:
            chosen = sorted(candidates, key=lambda t: t[0])[-1][1]

    # 組 TaxConstants
    brackets_raw = chosen.get("brackets_wan", [])
    brackets: List[tuple] = []
    for up, rate in brackets_raw:
        if isinstance(up, str) and up.lower() in ("inf", "infinite", "∞"):
            upper = float("inf")
        else:
            upper = float(up)
        brackets.append((upper, float(rate)))

    return TaxConstants(
        UNIT_FACTOR=float(chosen.get("unit_factor", 10000)),
        EXEMPT_AMOUNT=float(chosen["exempt_amount_wan"]),
        FUNERAL_EXPENSE=float(chosen["funeral_expense_wan"]),
        SPOUSE_DEDUCTION_VALUE=float(chosen["spouse_deduction_wan"]),
        ADULT_CHILD_DEDUCTION=float(chosen["adult_child_deduction_wan"]),
        PARENTS_DEDUCTION=float(chosen["parents_deduction_wan"]),
        DISABLED_DEDUCTION=float(chosen["disabled_deduction_wan"]),
        OTHER_DEPENDENTS_DEDUCTION=float(chosen["other_dependents_deduction_wan"]),
        TAX_BRACKETS=brackets,
        BUFFER_MULTIPLIER=float(chosen.get("buffer_multiplier", 1.10)),
        VERSION=str(chosen.get("version", "unversioned"))
    )
