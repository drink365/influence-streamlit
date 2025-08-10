from __future__ import annotations
from pathlib import Path
import base64
from typing import Dict, Any

TEMPLATE_DIR = Path("templates")
TEMPLATE_DIR.mkdir(parents=True, exist_ok=True)

def fig_to_data_uri(fig) -> str:
    import io
    buf = io.BytesIO()
    fig.savefig(buf, format="png", dpi=180, bbox_inches="tight")
    buf.seek(0)
    b64 = base64.b64encode(buf.read()).decode("ascii")
    return f"data:image/png;base64,{b64}"

def render_template(name: str, context: Dict[str, Any]) -> str:
    """偏好使用 jinja2；若無 jinja2，使用簡單替換。"""
    tpl_path = TEMPLATE_DIR / name
    html = tpl_path.read_text(encoding="utf-8")
    try:
        from jinja2 import Template  # type: ignore
        return Template(html).render(**context)
    except Exception:
        # fallback：非常簡單的 {{ key }} 取代
        for k, v in context.items():
            html = html.replace(f"{{{{ {k} }}}}", str(v))
        return html
