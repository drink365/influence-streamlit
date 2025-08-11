from __future__ import annotations
from typing import Optional, List, Dict
from datetime import datetime
import secrets

from src.db import get_conn

class ShareRepo:
    TBL = "shares"

    @staticmethod
    def create(case_id: str, advisor_id: str, *, days_valid: int = 14) -> Dict:
        conn = get_conn()
        now = datetime.utcnow()
        from datetime import timedelta
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
        row = cur.fetchone(); return dict(row) if row else None

    @staticmethod
    def list_by_advisor(advisor_id: str) -> List[Dict]:
        cur = get_conn().execute(
            f"SELECT * FROM {ShareRepo.TBL} WHERE advisor_id=? ORDER BY created_at DESC",
            (advisor_id,)
        )
        return [dict(r) for r in cur.fetchall()]

    @staticmethod
    def delete_by_token(token: str) -> bool:
        conn = get_conn()
        cur = conn.execute(f"DELETE FROM {ShareRepo.TBL} WHERE token=?", (token,))
        conn.commit()
        return cur.rowcount > 0

    @staticmethod
    def is_expired(row: Dict) -> bool:
        try:
            exp = row.get("expires_at")
            if not exp: return False
            return datetime.utcnow() > datetime.fromisoformat(exp)
        except Exception:
            return False
