# src/utils/nav.py
# 穩健跳頁：接受 'pages/5_Booking.py' 或側欄顯示名 'Booking' 都可
from __future__ import annotations
from typing import Optional

def goto(st, script_path_or_name: str, fallback_label: Optional[str] = None):
    """
    1) 直接試 switch_page(參數)
    2) 失敗→ get_pages() 以 script_path 對應 page_name 再跳
    3) 再試幾種名稱變形
    4) 最後給備援超連結（不讓頁面炸）
    """
    if not fallback_label:
        fallback_label = "前往指定頁"

    # 1) 已是正確頁名就會成功
    try:
        st.switch_page(script_path_or_name)
        return
    except Exception:
        pass

    # 2) 用官方索引把路徑轉頁名
    try:
        from streamlit.source_util import get_pages
        pages = get_pages("")  # 所有頁面資訊
        sp = script_path_or_name.replace("\\", "/")
        filename = sp.split("/")[-1]
        for _k, info in pages.items():
            sp_i = info.get("script_path", "").replace("\\", "/")
            if sp_i.endswith(sp) or sp_i.endswith(filename):
                name = info.get("page_name")
                if name:
                    st.switch_page(name)
                    return
    except Exception:
        pass

    # 3) 名稱變形（去副檔名、去排序碼、底線→空白）
    base = script_path_or_name.replace("\\", "/").split("/")[-1].replace(".py", "")
    try_names = [base, base.split("_", 1)[-1], base.replace("_", " ")]
    for name in try_names:
        try:
            st.switch_page(name)
            return
        except Exception:
            continue

    # 4) 備援：不拋錯，顯示連結
    guess = base.split("_", 1)[-1]
    try:
        st.warning("找不到指定頁面；已提供備援連結：")
        st.markdown(f"➡️ [{fallback_label}]({guess})")
    except Exception:
        pass


def goto_with_params(st, script_path_or_name: str, **params):
    """帶 QueryString 跳頁：先設參數，再呼叫 goto。"""
    try:
        st.query_params.update(params)
    except Exception:
        pass
    goto(st, script_path_or_name)
