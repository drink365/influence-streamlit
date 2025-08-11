from __future__ import annotations
from typing import Optional, Tuple
from datetime import datetime, timedelta
import json

from src.repos.credits_repo import CreditsRepo
from src.db import get_conn

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


def _has_recent_unlock(advisor_id: str, case_id: str, hours: int = 24) -> bool:
    conn = get_conn()
    since = (datetime.utcnow() - timedelta(hours=hours)).isoformat()
    cur = conn.execute(
        """
        SELECT 1 FROM credit_txns
        WHERE advisor_id=? AND reason='REPORT_FULL_UNLOCK' AND created_at>=?
        """,
        (advisor_id, since)
    )
    # 粗略以 24h 內解鎖任一案視為免重扣（若要精準到 case_id，請解析 meta）
    rows = cur.fetchall()
    return len(rows) > 0


def try_unlock_full_report(advisor_id: str, case_id: str) -> (bool, str):
    if _has_recent_unlock(advisor_id, case_id, hours=24):
        return True, "已於 24 小時內解鎖，免重複扣點。"
    ok = CreditsRepo.spend(advisor_id, REPORT_FULL_COST, "REPORT_FULL_UNLOCK", {"case_id": case_id})
    if not ok:
        return False, f"點數不足，需要 {REPORT_FULL_COST} 點。"
    return True, "解鎖成功：已扣點。"


def reward_won(advisor_id: str, case_id: str, premium: float):
    CreditsRepo.add(advisor_id, WON_REWARD, "WON_REWARD", {"case_id": case_id, "premium": premium})


def topup(advisor_id: str, amount: int, note: str = "TEST_TOPUP") -> int:
    return CreditsRepo.add(advisor_id, amount, note, {})
