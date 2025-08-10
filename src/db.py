from pathlib import Path
import sqlite3

DB_PATH = Path("data/app.db")
DB_PATH.parent.mkdir(parents=True, exist_ok=True)

SCHEMA_SQL = """
PRAGMA journal_mode=WAL;

CREATE TABLE IF NOT EXISTS cases (
  id TEXT PRIMARY KEY,
  advisor_id TEXT,
  advisor_name TEXT,
  client_alias TEXT,
  assets_financial REAL,
  assets_realestate REAL,
  assets_business REAL,
  liabilities REAL,
  net_estate REAL,
  tax_estimate REAL,
  liquidity_needed REAL,
  status TEXT DEFAULT 'Prospect',
  payload_json TEXT,
  created_at TEXT,
  updated_at TEXT
);

CREATE TABLE IF NOT EXISTS bookings (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  case_id TEXT,
  name TEXT,
  phone TEXT,
  email TEXT,
  timeslot TEXT,
  created_at TEXT,
  status TEXT DEFAULT 'Pending'
);

CREATE TABLE IF NOT EXISTS events (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  case_id TEXT,
  event TEXT,
  meta TEXT,
  created_at TEXT
);

CREATE TABLE IF NOT EXISTS shares (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  token TEXT UNIQUE,
  case_id TEXT,
  advisor_id TEXT,
  created_at TEXT,
  expires_at TEXT,
  opened_at TEXT,
  accepted_at TEXT
);

-- 新增：顧問點數錢包
CREATE TABLE IF NOT EXISTS wallets (
  advisor_id TEXT PRIMARY KEY,
  balance INTEGER DEFAULT 0,
  updated_at TEXT
);

-- 新增：點數交易記錄（正數=加點；負數=扣點）
CREATE TABLE IF NOT EXISTS credit_txns (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  advisor_id TEXT,
  change INTEGER,
  reason TEXT,
  meta TEXT,
  created_at TEXT
);
"""

_conn = None

def get_conn():
    global _conn
    if _conn is None:
        _conn = sqlite3.connect(DB_PATH.as_posix(), check_same_thread=False)
        _conn.row_factory = sqlite3.Row
        _conn.executescript(SCHEMA_SQL)
    return _conn

# =====================================
# src/repos/credits_repo.py（新增）
# =====================================
from __future__ import annotations
from typing import Optional, List, Dict
from datetime import datetime
import json

from src.db import get_conn

class CreditsRepo:
    @staticmethod
    def ensure_wallet(advisor_id: str):
        conn = get_conn()
        cur = conn.execute("SELECT advisor_id FROM wallets WHERE advisor_id=?", (advisor_id,))
        if not cur.fetchone():
            conn.execute(
                "INSERT INTO wallets (advisor_id, balance, updated_at) VALUES (?,?,?)",
                (advisor_id, 0, datetime.utcnow().isoformat()),
            )
            conn.commit()

    @staticmethod
    def get_balance(advisor_id: str) -> int:
        CreditsRepo.ensure_wallet(advisor_id)
        cur = get_conn().execute("SELECT balance FROM wallets WHERE advisor_id=?", (advisor_id,))
        row = cur.fetchone()
        return int(row[0]) if row else 0

    @staticmethod
    def add(advisor_id: str, amount: int, reason: str, meta: Optional[dict] = None) -> int:
        CreditsRepo.ensure_wallet(advisor_id)
        conn = get_conn()
        now = datetime.utcnow().isoformat()
        conn.execute(
            "INSERT INTO credit_txns (advisor_id, change, reason, meta, created_at) VALUES (?,?,?,?,?)",
            (advisor_id, int(amount), reason, json.dumps(meta or {}), now),
        )
        conn.execute(
            "UPDATE wallets SET balance = balance + ?, updated_at=? WHERE advisor_id=?",
            (int(amount), now, advisor_id),
        )
        conn.commit()
        return CreditsRepo.get_balance(advisor_id)

    @staticmethod
    def spend(advisor_id: str, amount: int, reason: str, meta: Optional[dict] = None) -> bool:
        CreditsRepo.ensure_wallet(advisor_id)
        conn = get_conn()
        cur = conn.execute("SELECT balance FROM wallets WHERE advisor_id=?", (advisor_id,))
        row = cur.fetchone(); bal = int(row[0]) if row else 0
        if bal < amount:
            return False
        now = datetime.utcnow().isoformat()
        import json as _json
        conn.execute(
            "INSERT INTO credit_txns (advisor_id, change, reason, meta, created_at) VALUES (?,?,?,?,?)",
            (advisor_id, -int(amount), reason, _json.dumps(meta or {}), now),
        )
        conn.execute(
            "UPDATE wallets SET balance = balance - ?, updated_at=? WHERE advisor_id=?",
            (int(amount), now, advisor_id),
        )
        conn.commit()
        return True

    @staticmethod
    def list_txns(advisor_id: str) -> List[Dict]:
        cur = get_conn().execute(
            "SELECT * FROM credit_txns WHERE advisor_id=? ORDER BY created_at DESC",
            (advisor_id,)
        )
        return [dict(r) for r in cur.fetchall()]
