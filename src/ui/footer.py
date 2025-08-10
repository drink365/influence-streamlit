import streamlit as st

def footer():
    st.markdown("---")
    st.markdown(
        """
        <div style='display:flex;justify-content:center;gap:1.5em;font-size:14px;color:gray;'>
          <a href='?' style='color:#006666;text-decoration:underline;'>《影響力》傳承策略平台</a>
          <a href='https://gracefo.com' target='_blank'>永傳家族辦公室</a>
          <a href='mailto:123@gracefo.com'>123@gracefo.com</a>
        </div>
        """,
        unsafe_allow_html=True
    )
