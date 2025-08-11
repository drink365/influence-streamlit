from __future__ import annotations
from typing import Dict, Any
from src.repos.event_repo import EventRepo


def log_safe(case_id: str, event: str, meta: Dict[str, Any]):
    try:
        EventRepo.log(case_id, event, meta)
    except Exception:
        # 靜默失敗，避免中斷主要流程
        pass
