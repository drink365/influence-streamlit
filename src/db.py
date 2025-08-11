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

CREATE TABLE IF NOT EXISTS wallets (
  advisor_id TEXT PRIMARY KEY,
  balance INTEGER DEFAULT 0,
  updated_at TEXT
);

CREATE TABLE IF NOT EXISTS credit_txns (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  advisor_id TEXT,
  change INTEGER,
  reason TEXT,
  meta TEXT,
  created_at TEXT
);

-- 索引（避免重複建立）
CREATE INDEX IF NOT EXISTS idx_events_case ON events(case_id, created_at);
CREATE INDEX IF NOT EXISTS idx_shares_token ON shares(token);
CREATE INDEX IF NOT EXISTS idx_shares_adv ON shares(advisor_id, created_at);
CREATE INDEX IF NOT EXISTS idx_txns_adv ON credit_txns(advisor_id, created_at);
"""

_conn = None

def get_conn():
    global _conn
    if _conn is None:
        _conn = sqlite3.connect(DB_PATH.as_posix(), check_same_thread=False)
        _conn.row_factory = sqlite3.Row
        _conn.executescript(SCHEMA_SQL)
    return _conn
