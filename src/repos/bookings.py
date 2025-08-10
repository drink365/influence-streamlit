# src/repos/bookings.py
from __future__ import annotations
from dataclasses import dataclass, asdict
from pathlib import Path
from typing import List, Dict, Any, Optional
import csv

from src.config import DATA_DIR

FIELDS = [
    "booking_id",   # BOOK-YYYYMMDD-XXXX
    "ts",           # 2025-08-10 14:32:01 CST
    "case_id",      # 對應個案編號，可為空
    "name",
    "email",
    "mobile",
    "preferred_time",
    "need",
    "status",       # new / contacted / scheduled / done / cancelled
]

@dataclass
class Booking:
    booking_id: str
    ts: str
    case_id: str
    name: str
    email: str
    mobile: str
    preferred_time: str
    need: str
    status: str = "new"

class BookingsRepo:
    def __init__(self, filename: str = "bookings.csv"):
        self.path = Path(DATA_DIR) / filename
        self.path.parent.mkdir(parents=True, exist_ok=True)
        if not self.path.exists():
            with self.path.open("w", encoding="utf-8", newline="") as f:
                writer = csv.DictWriter(f, fieldnames=FIELDS)
                writer.writeheader()

    def add(self, row: Dict[str, Any] | Booking) -> None:
        if isinstance(row, Booking):
            row = asdict(row)
        # 僅保留標準欄位，避免寫入多餘 keys
        clean = {k: (row.get(k, "") if row.get(k) is not None else "") for k in FIELDS}
        with self.path.open("a", encoding="utf-8", newline="") as f:
            writer = csv.DictWriter(f, fieldnames=FIELDS)
            writer.writerow(clean)

    def list_all(self) -> List[Dict[str, str]]:
        with self.path.open("r", encoding="utf-8", newline="") as f:
            return list(csv.DictReader(f))

    def get_by_id(self, booking_id: str) -> Optional[Dict[str, str]]:
        with self.path.open("r", encoding="utf-8", newline="") as f:
            for row in csv.DictReader(f):
                if row.get("booking_id") == booking_id:
                    return row
        return None

    def update_status(self, booking_id: str, new_status: str) -> bool:
        rows = self.list_all()
        updated = False
        for r in rows:
            if r.get("booking_id") == booking_id:
                r["status"] = new_status
                updated = True
                break
        if updated:
            with self.path.open("w", encoding="utf-8", newline="") as f:
                writer = csv.DictWriter(f, fieldnames=FIELDS)
                writer.writeheader()
                writer.writerows(rows)
        return updated
