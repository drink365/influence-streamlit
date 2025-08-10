from pathlib import Path
import csv, os
from src.config import DATA_DIR

HEADERS = ["ts","name","phone","email","notes","status"]

class BookingRepo:
    def __init__(self):
        self.path = Path(DATA_DIR) / "bookings.csv"
        os.makedirs(DATA_DIR, exist_ok=True)

    def add(self, row: dict):
        need_header = not self.path.exists()
        with self.path.open("a", newline="", encoding="utf-8") as f:
            w = csv.DictWriter(f, fieldnames=HEADERS)
            if need_header: w.writeheader()
            w.writerow({k: row.get(k, "") for k in HEADERS})

    def get_all(self):
        if not self.path.exists(): return []
        with self.path.open("r", newline="", encoding="utf-8") as f:
            return list(csv.DictReader(f))
