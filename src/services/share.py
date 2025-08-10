from __future__ import annotations
from typing import Dict

from src.repos.share_repo import ShareRepo
from src.repos.case_repo import CaseRepo
from src.repos.event_repo import EventRepo

def create_share(case_id: str, advisor_id: str, *, days_valid: int = 14) -> Dict:
    case = CaseRepo.get(case_id)
    if not case:
        raise ValueError("找不到 Case")
    data = ShareRepo.create(case_id, advisor_id, days_valid=days_valid)
    EventRepo.log(case_id, "SHARE_CREATED", {"token": data["token"], "days_valid": days_valid})
    return data

def record_open(token: str):
    row = ShareRepo.get_by_token(token)
    if not row: 
        return
    ShareRepo.mark_opened(token)
    EventRepo.log(row["case_id"], "SHARE_OPENED", {"token": token})

def record_accept(token: str):
    row = ShareRepo.get_by_token(token)
    if not row: 
        return
    ShareRepo.mark_accepted(token)
    EventRepo.log(row["case_id"], "SHARE_ACCEPTED", {"token": token})
