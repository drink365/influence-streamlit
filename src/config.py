import os, streamlit as st
from pathlib import Path

def _get(k, default=None):
    try:
        return st.secrets.get(k, os.environ.get(k, default))
    except Exception:
        return os.environ.get(k, default)

ADMIN_KEY = _get("ADMIN_KEY", "demo")

SMTP = {
    "host": _get("SMTP_HOST", "smtp.gmail.com"),
    "port": int(_get("SMTP_PORT", "587")),
    "user": _get("SMTP_USER"),
    "pass": _get("SMTP_PASS"),
    "from": _get("MAIL_FROM", _get("SMTP_USER")),
    "from_name": _get("MAIL_FROM_NAME", "永傳家族辦公室"),
    "reply_to": _get("MAIL_REPLY_TO"),
    "to_admin": _get("MAIL_TO_ADMIN"),
}

DATA_DIR = Path("data")
DATA_DIR.mkdir(parents=True, exist_ok=True)
