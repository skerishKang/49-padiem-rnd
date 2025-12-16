import streamlit as st
from pathlib import Path
from frontend_unified.utils.i18n import get_text
from frontend_unified.sidebar import render_sidebar

st.set_page_config(
    page_title=get_text("general_page_title"),
    page_icon="🎬",
    layout="wide",
    initial_sidebar_state="expanded",
)

render_sidebar()

# Import from the UNIFIED utils/steps to ensure we use the new port config
from frontend_unified.utils.ui_utils import build_theme_assets
from frontend_unified.utils.config_utils import load_session_data
from frontend_unified.steps import (
    audio,
    stt,
    text_process,
    tts,
    xtts,
    rvc,
    lipsync,
    pipeline
)

# === Initialization ===
build_theme_assets()

if "current_run_name" not in st.session_state:
    st.session_state["current_run_name"] = "default_run"

# === Sidebar: Guide & Workspace ===
# These append to the sidebar created by render_sidebar
with st.sidebar:
    st.title("가이드 (Guide)")
    st.info("""
    **단계별 진행 가이드**:
    1. **오디오 추출**: 영상에서 음성을 분리합니다.
    2. **STT**: 음성을 텍스트로 변환합니다.
    3. **텍스트 처리**: 번역 및 교정을 수행합니다.
    4. **TTS**: 텍스트를 음성으로 변환합니다.
    5. **RVC**: 목소리를 변조합니다.
    6. **립싱크**: 영상의 입모양을 맞춥니다.
    """)
    st.markdown("---")
    
    st.title(get_text("workspace_title"))
    st.caption("파일을 업로드하면 자동으로 생성되는 결과물 저장 폴더입니다.")
    run_base_dir = st.text_input(
        get_text("run_base_dir"), 
        value="data/runs/sample",
        help="이 폴더에 모든 작업 결과물이 저장됩니다. 다른 작업을 할 때는 폴더명을 변경하여 결과물이 섞이지 않게 하세요."
    )
    
    if run_base_dir != st.session_state.get("run_base_dir"):
        st.session_state["run_base_dir"] = run_base_dir
        load_session_data(run_base_dir)
    
    st.markdown("---")
    st.subheader(get_text("status_title"))
    if "last_audio_input_media" in st.session_state:
        st.info(f"{get_text('input_label')}{Path(st.session_state['last_audio_input_media']).name}")

# === Main Header ===
st.title(get_text("general_page_title"))
st.markdown(get_text("general_page_desc"))

# === Render Steps ===
pipeline.render()
st.markdown("---")
st.subheader(get_text("step_detail_title"))
audio.render()
stt.render()
text_process.render()
tts.render()
xtts.render()
rvc.render()
lipsync.render()
