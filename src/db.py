from pathlib import Path
import sqlite3

DB_PATH = Path("data/app.db")
DB_PATH.parent.mkdir(parents=True, exist_ok=True)

SCHEMA_SQL = """
PRAGMA journal_mode=WAL;

CREATE TABLE IF NOT EXISTS cases (
  id TEXT PRIMARY KEY,             -- Case ID（CASE-YYYYMMDD-XXXX）
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
  status TEXT DEFAULT 'Prospect',  -- Prospect/In Progress/Won/Lost
  payload_json TEXT,               -- 原始計算與參數 JSON
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
  event TEXT,         -- e.g. DIAG_DONE, REPORT_UNLOCKED, WON_REPORTED
  meta TEXT,          -- JSON
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
