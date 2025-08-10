from datetime import datetime
from src.db import get_conn

class BookingRepo:
    TBL = "bookings"

    @staticmethod
    def create(payload: dict):
        conn = get_conn()
        now = datetime.utcnow().isoformat()
        cur = conn.execute(
            f"""
            INSERT INTO {BookingRepo.TBL}
            (case_id, name, phone, email, timeslot, created_at, status)
            VALUES (?,?,?,?,?,?,?)
            """,
            (
                payload.get("case_id"), payload.get("name"), payload.get("phone"), payload.get("email"),
                payload.get("timeslot"), now, payload.get("status","Pending"),
            ),
        )
        conn.commit()
        return cur.lastrowid
