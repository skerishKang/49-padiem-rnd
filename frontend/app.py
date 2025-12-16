import streamlit as st
import os
from pathlib import Path

# 페이지 설정 (가장 먼저 호출)
st.set_page_config(
    page_title="AI Dubbing Pipeline",
    page_icon="🎙️",
    layout="wide",
    initial_sidebar_state="expanded",
)

# 유틸리티 및 스텝 모듈 임포트
from frontend.utils.ui_utils import build_theme_assets
from frontend.utils.config_utils import load_session_data, save_session_data
from frontend.steps import (
    audio,
    stt,
    text_process,
    tts,
    xtts,
    rvc,
    lipsync,
    pipeline
)

# === 초기화 및 설정 ===
build_theme_assets()

if "current_run_name" not in st.session_state:
    st.session_state["current_run_name"] = "default_run"

# === 사이드바: 파일 히스토리 ===
st.sidebar.title("📂 최근 작업 파일")
run_base_dir = st.sidebar.text_input("작업 폴더 (Run Base Dir)", value="data/runs/sample")

# 작업 폴더가 변경되면 세션 데이터 로드
if run_base_dir != st.session_state.get("run_base_dir"):
    st.session_state["run_base_dir"] = run_base_dir
    load_session_data(run_base_dir)

st.sidebar.markdown("---")
st.sidebar.subheader("상태 정보")
if "last_audio_input_media" in st.session_state:
    st.sidebar.info(f"입력: {Path(st.session_state['last_audio_input_media']).name}")

# === 메인 헤더 ===
st.title("🎙️ AI Dubbing Pipeline")
st.markdown("""
이 파이프라인은 **오디오 추출 -> STT -> 번역/교정 -> TTS -> RVC -> LipSync** 과정을 순차적으로 수행합니다.
각 단계는 독립적으로 실행하거나, 설정을 마친 후 전체 파이프라인을 한 번에 실행할 수 있습니다.
""")

# === 단계별 렌더링 ===
audio.render()
stt.render()
text_process.render()
tts.render()
xtts.render()
rvc.render()
lipsync.render()
pipeline.render()

# === 하단 정보 ===
st.markdown("---")
st.caption("© 2024 AI Dubbing Pipeline | Powered by Streamlit")
