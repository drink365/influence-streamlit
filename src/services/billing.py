from __future__ import annotations
from typing import Optional

from src.repos.credits_repo import CreditsRepo

# 可在 secrets 設定：
# [CREDITS]
# REPORT_FULL_COST = 5
# WON_REWARD = 5

def _cfg_int(section: str, key: str, default: int) -> int:
    try:
        import streamlit as st
        return int(st.secrets.get(section, {}).get(key, default))
    except Exception:
        return default

REPORT_FULL_COST = _cfg_int("CREDITS", "REPORT_FULL_COST", 5)
WON_REWARD = _cfg_int("CREDITS", "WON_REWARD", 5)


def balance(advisor_id: str) -> int:
    return CreditsRepo.get_balance(advisor_id)


def try_unlock_full_report(advisor_id: str, case_id: str) -> (bool, str):
    ok = CreditsRepo.spend(advisor_id, REPORT_FULL_COST, "REPORT_FULL_UNLOCK", {"case_id": case_id})
    if not ok:
        return False, f"點數不足，需要 {REPORT_FULL_COST} 點。"
    return True, "解鎖成功：已扣點。"


def reward_won(advisor_id: str, case_id: str, premium: float):
    CreditsRepo.add(advisor_id, WON_REWARD, "WON_REWARD", {"case_id": case_id, "premium": premium})


def topup(advisor_id: str, amount: int, note: str = "TEST_TOPUP") -> int:
    return CreditsRepo.add(advisor_id, amount, note, {})
