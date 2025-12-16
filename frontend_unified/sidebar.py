import streamlit as st

def render_sidebar():
    """Renders the custom sidebar with language toggle and navigation."""
    
    # Initialize language state if not present
    if "ui_lang" not in st.session_state:
        st.session_state["ui_lang"] = "한국어"

    with st.sidebar:
        st.header("메뉴 (Menu)")
        
        # Language Toggle
        lang = st.radio(
            "Language", 
            ["한국어", "English"], 
            index=0 if st.session_state["ui_lang"] == "한국어" else 1, 
            horizontal=True,
            key="sidebar_lang_toggle"
        )
        st.session_state["ui_lang"] = lang
        
        st.markdown("---")
        
        # Navigation
        if lang == "한국어":
            st.page_link("Home.py", label="홈", icon="🏠")
            st.page_link("pages/1_🎙️_실시간_통역.py", label="실시간 통역", icon="🎙️")
            st.page_link("pages/2_🎬_일반_더빙.py", label="일반 더빙", icon="🎬")
            st.page_link("pages/3_⚡_고속_더빙.py", label="고속 더빙", icon="⚡")
        else:
            st.page_link("Home.py", label="Home", icon="🏠")
            st.page_link("pages/1_🎙️_실시간_통역.py", label="Live Interpretation", icon="🎙️")
            st.page_link("pages/2_🎬_일반_더빙.py", label="General Dubbing", icon="🎬")
            st.page_link("pages/3_⚡_고속_더빙.py", label="High Speed Dubbing", icon="⚡")
            
        st.markdown("---")
