from __future__ import annotations
from pathlib import Path
from typing import Dict, Any
import base64

BRAND_PATH = Path("brand.json")

DEFAULT_BRAND = {
    "name": "永傳家族辦公室",
    "primary_color": "#0F766E",   # teal-700
    "accent_color": "#F59E0B",    # amber-500
    "text_color": "#222222",
    "logo_path": "",              # 可放 ./assets/logo.png
    "contact": {
        "company": "永傳家族辦公室",
        "address": "台北市中山區南京東路路二段101號9樓",
        "email": "123@gracefo.com",
        "website": "https://gracefo.com",
        "booking_url": "https://gracefo.com/booking"
    }
}


def load_brand() -> Dict[str, Any]:
    try:
        if BRAND_PATH.exists():
            import json
            data = json.loads(BRAND_PATH.read_text(encoding="utf-8"))
            return {**DEFAULT_BRAND, **data}
    except Exception:
        pass
    return DEFAULT_BRAND


def logo_data_uri(brand: Dict[str, Any]) -> str | None:
    p = brand.get("logo_path") or ""
    if not p:
        return None
    path = Path(p)
    if not path.exists():
        return None
    try:
        b64 = base64.b64encode(path.read_bytes()).decode("ascii")
        mime = "image/png" if path.suffix.lower() in [".png"] else "image/jpeg"
        return f"data:{mime};base64,{b64}"
    except Exception:
        return None
