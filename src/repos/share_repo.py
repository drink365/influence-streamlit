from __future__ import annotations
from typing import Optional, List, Dict
from datetime import datetime, timedelta
import secrets

from src.db import get_conn

class ShareRepo:
    TBL = "shares"

    @staticmethod
    def create(case_id: str, advisor_id: str, *, days_valid: int = 14) -> Dict:
        conn = get_conn()
        now = datetime.utcnow()
        token = secrets.token_urlsafe(16)
        exp = now + timedelta(days=days_valid)
        conn.execute(
            f"""
            INSERT INTO {ShareRepo.TBL} (token, case_id, advisor_id, created_at, expires_at)
            VALUES (?,?,?,?,?)
            """,
            (token, case_id, advisor_id, now.isoformat(), exp.isoformat()),
        )
        conn.commit()
        return {
            "token": token,
            "case_id": case_id,
            "advisor_id": advisor_id,
            "created_at": now.isoformat(),
            "expires_at": exp.isoformat(),
        }

    @staticmethod
    def get_by_token(token: str) -> Optional[Dict]:
        cur = get_conn().execute(f"SELECT * FROM {ShareRepo.TBL} WHERE token=?", (token,))
        row = cur.fetchone()
        return dict(row) if row else None

    @staticmethod
    def list_by_advisor(advisor_id: str) -> List[Dict]:
        cur = get_conn().execute(
            f"SELECT * FROM {ShareRepo.TBL} WHERE advisor_id=? ORDER BY created_at DESC",
            (advisor_id,)
        )
        return [dict(r) for r in cur.fetchall()]

    @staticmethod
    def mark_opened(token: str):
        get_conn().execute(
            f"UPDATE {ShareRepo.TBL} SET opened_at=? WHERE token=? AND opened_at IS NULL",
            (datetime.utcnow().isoformat(), token)
        ).connection.commit()

    @staticmethod
    def mark_accepted(token: str):
        get_conn().execute(
            f"UPDATE {ShareRepo.TBL} SET accepted_at=? WHERE token=? AND accepted_at IS NULL",
            (datetime.utcnow().isoformat(), token)
        ).connection.commit()
