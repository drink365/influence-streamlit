import re
from datetime import datetime, timezone

def utc_now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()

# 基本驗證
EMAIL_RE = re.compile(r"[^@\s]+@[^@\s]+\.[^@\s]+")
PHONE_RE = re.compile(r"[0-9+\-\s]{8,}")

def valid_email(s: str) -> bool:
    return bool(EMAIL_RE.fullmatch((s or "").strip()))

def valid_phone(s: str) -> bool:
    return bool(PHONE_RE.fullmatch((s or "").strip()))
