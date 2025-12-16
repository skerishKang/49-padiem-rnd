import streamlit as st
from frontend_unified.sidebar import render_sidebar

st.set_page_config(
    page_title="고속 더빙",
    page_icon="⚡",
    layout="wide",
    initial_sidebar_state="expanded"
)

render_sidebar()

st.title("⚡ 고속 더빙")

st.info("이 모듈은 현재 개발 중입니다. Gemini App의 고속 파일 처리 기능을 통합할 예정입니다.")

uploaded_file = st.file_uploader("비디오/오디오 업로드", type=["mp4", "mp3", "wav", "m4a"])

if uploaded_file:
    st.success(f"파일 업로드됨: {uploaded_file.name}")
    st.button("🚀 고속 더빙 시작 (준비 중)")
