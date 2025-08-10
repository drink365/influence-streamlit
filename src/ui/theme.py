# src/ui/theme.py
import streamlit as st

BRAND_PRIMARY = "#0A6C74"
BRAND_ACCENT = "#00A6A6"

def inject_css():
    st.markdown(
        f"""
        <style>
          /* 全站字級與留白 */
          .block-container {{ padding-top: 2rem; padding-bottom: 4rem; max-width: 1200px; }}
          h1, h2, h3 {{ letter-spacing: .2px; }}
          /* 卡片 */
          .yc-card {{
            border-radius: 16px; padding: 18px 18px;
            background: #fff; box-shadow: 0 6px 26px rgba(10,108,116,0.08);
            border: 1px solid rgba(10,108,116,0.08);
          }}
          .yc-badge {{
            display:inline-block; padding:6px 10px; border-radius:999px;
            background:{BRAND_ACCENT}14; color:{BRAND_PRIMARY}; font-size:12px; font-weight:600;
            border:1px solid {BRAND_ACCENT}55;
          }}
          .yc-cta button[kind="primary"] {{
            border-radius: 999px !important; padding: .6rem 1rem !important; font-weight:700 !important;
          }}
          .yc-ghost button {{
            border:1px solid {BRAND_PRIMARY}55 !important; color:{BRAND_PRIMARY} !important; background:#fff !important;
          }}
          /* 清單行距 */
          ul, ol {{ line-height:1.7; }}
          /* 置中容器 */
          .yc-center {{ display:flex; align-items:center; justify-content:center; gap:.75rem; }}
        </style>
        """,
        unsafe_allow_html=True,
    )

def hero(title: str, subtitle: str):
    st.markdown(
        f"""
        <div class="yc-card" style="padding:28px 28px; background:linear-gradient(180deg,#F8FBFC 0%, #FFFFFF 100%);">
          <div class="yc-badge">傳承策略平台</div>
          <h1 style="margin:.6rem 0 0; font-size:32px;">{title}</h1>
          <p style="color:#4a4a4a; font-size:16px; margin:.4rem 0 1rem;">{subtitle}</p>
        </div>
        """,
        unsafe_allow_html=True,
    )

def section_title(kicker: str, title: str):
    st.markdown(
        f"""
        <div style="margin-top:1.4rem">
          <div class="yc-badge">{kicker}</div>
          <h2 style="margin:.5rem 0 .8rem; font-size:24px;">{title}</h2>
        </div>
        """,
        unsafe_allow_html=True,
    )

def card(title: str, body: str):
    st.markdown(
        f"""
        <div class="yc-card">
          <h4 style="margin:.2rem 0 .4rem; font-size:18px;">{title}</h4>
          <div style="color:#444; font-size:14px;">{body}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )
