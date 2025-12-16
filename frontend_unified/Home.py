import streamlit as st
from pathlib import Path
import sys
from dotenv import load_dotenv

ROOT_DIR = Path(__file__).resolve().parent.parent
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

# 레포 루트에 있는 .env 파일을 자동으로 로드
load_dotenv(ROOT_DIR / ".env")

from frontend_unified.utils.i18n import get_text
from frontend_unified.sidebar import render_sidebar

st.set_page_config(
    page_title=get_text("page_title"),
    page_icon="🎙️",
    layout="wide",
    initial_sidebar_state="expanded",
)

# Render Sidebar (handles language toggle and nav)
render_sidebar()

# Custom CSS for the launcher cards
st.markdown("""
<style>
    .launcher-card {
        background-color: #262730;
        border-radius: 1rem;
        padding: 2rem;
        text-align: center;
        border: 1px solid #4e4f57;
        transition: transform 0.2s, border-color 0.2s;
        height: 100%;
        display: flex;
        flex-direction: column;
        justify-content: center;
        align-items: center;
        cursor: pointer;
    }
    .launcher-card:hover {
        transform: translateY(-5px);
        border-color: #ff4b4b;
        box-shadow: 0 4px 15px rgba(0,0,0,0.3);
    }
    .card-icon {
        font-size: 4rem;
        margin-bottom: 1rem;
    }
    .card-title {
        font-size: 1.5rem;
        font-weight: bold;
        margin-bottom: 0.5rem;
        color: #ffffff;
    }
    .card-desc {
        color: #a0a0a0;
        font-size: 1rem;
        font-weight: bold;
    }
    /* Hide default sidebar nav for a cleaner launcher look */
    [data-testid="stSidebarNav"] {
        display: none;
    }
</style>
""", unsafe_allow_html=True)

st.title(get_text("main_title"))
st.markdown(get_text("select_mode"))
st.markdown("---")

col1, col2, col3 = st.columns(3)

with col1:
    with st.container(border=True):
        st.markdown(f"""
        <div style="text-align: center; padding: 20px;">
            <div style="font-size: 60px; margin-bottom: 10px;">🎙️</div>
            <h3>{get_text("live_mode_title")}</h3>
            <p style="color: #aaa;">{get_text("live_mode_desc")}</p>
        </div>
        """, unsafe_allow_html=True)
        if st.button(get_text("live_mode_btn"), use_container_width=True):
            st.switch_page("pages/1_🎙️_실시간_통역.py")

with col2:
    with st.container(border=True):
        st.markdown(f"""
        <div style="text-align: center; padding: 20px;">
            <div style="font-size: 60px; margin-bottom: 10px;">🎬</div>
            <h3>{get_text("general_mode_title")}</h3>
            <p style="color: #aaa;">{get_text("general_mode_desc")}</p>
        </div>
        """, unsafe_allow_html=True)
        if st.button(get_text("general_mode_btn"), use_container_width=True):
            st.switch_page("pages/2_🎬_일반_더빙.py")

with col3:
    with st.container(border=True):
        st.markdown(f"""
        <div style="text-align: center; padding: 20px;">
            <div style="font-size: 60px; margin-bottom: 10px;">⚡</div>
            <h3>{get_text("speed_mode_title")}</h3>
            <p style="color: #aaa;">{get_text("speed_mode_desc")}</p>
        </div>
        """, unsafe_allow_html=True)
        if st.button(get_text("speed_mode_btn"), use_container_width=True):
            st.switch_page("pages/3_⚡_고속_더빙.py")

st.markdown("---")
st.caption(get_text("footer_caption"))
