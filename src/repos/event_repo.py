import json
from datetime import datetime
from src.db import get_conn

class EventRepo:
    TBL = "events"

    @staticmethod
    def log(case_id: str, event: str, meta: dict | None = None):
        get_conn().execute(
            f"INSERT INTO {EventRepo.TBL} (case_id, event, meta, created_at) VALUES (?,?,?,?)",
            (case_id, event, json.dumps(meta or {}, ensure_ascii=False), datetime.utcnow().isoformat()),
        ).connection.commit()
