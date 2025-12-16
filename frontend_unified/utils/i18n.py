import streamlit as st

# Dictionary of translations
TRANSLATIONS = {
    "en": {
        "page_title": "AI Dubbing & Interpretation",
        "main_title": "🚀 AI Dubbing & Interpretation Studio",
        "select_mode": "### Select Your Mode",
        "live_mode_title": "Live Interpretation",
        "live_mode_desc": "Real-time voice translation and interpretation.",
        "live_mode_btn": "Start Live Mode",
        "general_mode_title": "General Dubbing",
        "general_mode_desc": "Professional pipeline with granular control.",
        "general_mode_btn": "Start Studio Mode",
        "speed_mode_title": "High-Speed Dubbing",
        "speed_mode_desc": "Fast, automated dubbing processing.",
        "speed_mode_btn": "Start High-Speed Mode",
        "footer_caption": "Select a module to proceed. You can return here anytime via the sidebar.",
        "sidebar_lang_select": "Language / 언어",
        "back_to_launcher": "🏠 Back to Launcher",
        "general_page_title": "🎬 General Dubbing Studio",
        "general_page_desc": """
        Professional pipeline with granular control over every step.
        **Audio Extraction -> STT -> Translation -> TTS -> RVC -> LipSync**
        """,
        "full_pipeline_title": "Full Pipeline Execution",
        "full_pipeline_desc": "Execute selected steps sequentially.",
        "input_media_select": "Select Input Media",
        "input_media_manual": "Manual Input Path",
        "run_base_dir": "Run Base Directory",
        "select_steps": "**Select Steps to Run**",
        "run_selected_steps": "Run Selected Steps",
        "step_stt": "STT",
        "step_text": "Text Processing",
        "step_tts": "TTS",
        "step_rvc": "RVC",
        "step_lipsync": "LipSync",
        "stt_method_select": "Select STT Method",
        "tts_method_select": "Select TTS Method",
        "stt_whisper": "Whisper (Local)",
        "stt_gemini": "Gemini 2.5 Flash (Cloud/Fast)",
        "tts_vallex": "VALL-E X (Local)",
        "tts_gemini": "Gemini 2.5 Flash TTS (Cloud/Fast)",
        "success_pipeline": "Selected pipeline steps completed.",
        "error_pipeline": "Error occurred in step: ",
        "workspace_title": "📂 Project Workspace",
        "status_title": "Status",
        "input_label": "Input: ",
        "step_detail_title": "Detailed Step Execution"
    },
    "ko": {
        "page_title": "AI 더빙 & 통역",
        "main_title": "🚀 AI 더빙 & 통역 스튜디오",
        "select_mode": "### 원하시는 모드를 선택하세요",
        "live_mode_title": "실시간 통역",
        "live_mode_desc": "실시간 음성 번역 및 통역을 제공합니다.",
        "live_mode_btn": "실시간 모드 시작",
        "general_mode_title": "일반 더빙",
        "general_mode_desc": "세밀한 제어가 가능한 전문 더빙 파이프라인입니다.",
        "general_mode_btn": "스튜디오 모드 시작",
        "speed_mode_title": "고속 더빙",
        "speed_mode_desc": "빠르고 자동화된 더빙 처리를 지원합니다.",
        "speed_mode_btn": "고속 모드 시작",
        "footer_caption": "원하는 모듈을 선택하여 진행하세요. 사이드바를 통해 언제든지 이 화면으로 돌아올 수 있습니다.",
        "sidebar_lang_select": "언어 / Language",
        "back_to_launcher": "🏠 런처로 돌아가기",
        "general_page_title": "🎬 일반 더빙 스튜디오",
        "general_page_desc": """
        더빙 프로세스의 모든 단계를 세밀하게 제어할 수 있는 전문 파이프라인입니다.
        **오디오 추출 -> STT -> 번역 -> TTS -> RVC -> 립싱크**
        """,
        "full_pipeline_title": "전체 파이프라인 실행",
        "full_pipeline_desc": "선택한 단계들을 순차적으로 실행합니다.",
        "input_media_select": "입력 미디어 선택",
        "input_media_manual": "입력 미디어 경로 직접 입력",
        "run_base_dir": "실행 결과 기준 폴더",
        "select_steps": "**실행할 단계 선택**",
        "run_selected_steps": "선택한 단계 실행",
        "step_stt": "STT",
        "step_text": "텍스트 처리",
        "step_tts": "TTS",
        "step_rvc": "RVC",
        "step_lipsync": "LipSync",
        "stt_method_select": "STT 방식 선택",
        "tts_method_select": "TTS 방식 선택",
        "stt_whisper": "Whisper (로컬)",
        "stt_gemini": "Gemini 2.5 Flash (클라우드/고속)",
        "tts_vallex": "VALL-E X (로컬)",
        "tts_gemini": "Gemini 2.5 Flash TTS (클라우드/고속)",
        "success_pipeline": "선택한 파이프라인 단계 실행이 완료되었습니다.",
        "error_pipeline": "단계에서 오류가 발생했습니다: ",
        "workspace_title": "📂 프로젝트 작업 공간",
        "status_title": "상태",
        "input_label": "입력: ",
        "step_detail_title": "단계별 상세 실행"
    }
}

def init_language_state():
    if "language" not in st.session_state:
        st.session_state["language"] = "ko" # Default to Korean

def get_text(key):
    lang = st.session_state.get("language", "ko")
    return TRANSLATIONS.get(lang, TRANSLATIONS["ko"]).get(key, key)

def render_language_selector():
    init_language_state()
    st.sidebar.markdown("---")
    lang_options = {"한국어": "ko", "English": "en"}
    
    # Find index of current language
    current_lang = st.session_state["language"]
    index = list(lang_options.values()).index(current_lang)
    
    selected_label = st.sidebar.selectbox(
        get_text("sidebar_lang_select"),
        options=list(lang_options.keys()),
        index=index,
        key="lang_selector"
    )
    
    # Update session state if changed
    new_lang = lang_options[selected_label]
    if new_lang != st.session_state["language"]:
        st.session_state["language"] = new_lang
        st.rerun()
