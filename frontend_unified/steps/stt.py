import streamlit as st
from frontend_unified.utils.ui_utils import handle_file_input, text_input_with_state, display_stt_result
from frontend_unified.utils.api_utils import execute_step
from frontend_unified.utils.config_utils import update_run_defaults, build_override_config, cleanup_temp_file, save_session_data, update_output_path_from_input
from frontend_unified.constants import DEFAULT_STT_CONFIG_PATH, STT_UI_OVERRIDE_PATH, LANGUAGE_OPTIONS, LANGUAGE_LABEL
from frontend_unified.utils.i18n import get_text
import json
import tempfile

def render():
    with st.expander("STT (Speech-to-Text)", expanded=True):
        st.write("음성을 텍스트로 변환합니다.")
        
        stt_method = st.radio(
            get_text("stt_method_select"),
            [get_text("stt_whisper"), get_text("stt_gemini")],
            index=0,
            horizontal=True
        )

        col_input, col_config = st.columns([2, 1])

        with col_input:
            st.markdown("**입력/출력 파일**")
            # 오디오 추출 단계에서 설정한 STT 입력 오디오 경로를 기본값으로 사용
            default_stt_input = st.session_state.get("stt_input_audio_path", "data/intermediates/source_audio.wav")
            input_audio = handle_file_input(
                "STT 입력 오디오 경로",
                "stt_input_audio_path",
                default_stt_input,
                "STT 입력 오디오 업로드",
                ["wav", "mp3", "flac", "m4a"],
            )

            # 변경 감지
            if input_audio != st.session_state.get("last_stt_input_audio"):
                st.session_state["last_stt_input_audio"] = input_audio

            # 입력 오디오 경로 기반으로 STT 결과 JSON 경로를 자동으로 제안
            update_output_path_from_input(input_audio, "stt_output_path", "_stt.json")

            # update_run_defaults 또는 위에서 계산한 stt_output_path를 기본값으로 사용
            default_stt_output = st.session_state.get("stt_output_path", "data/intermediates/stt_result.json")
            stt_output = text_input_with_state(
                "STT 결과 JSON 경로",
                "stt_output_path",
                default_stt_output,
            )

        with col_config:
            st.markdown("**설정**")
            if "Whisper" in stt_method:
                st.caption("기본적으로 auto 감지를 사용하며, 필요 시 언어와 설정 파일을 지정하세요.")
                stt_config = handle_file_input(
                    "STT 설정 파일 경로",
                    "stt_config",
                    str(DEFAULT_STT_CONFIG_PATH),
                    "STT 설정 업로드(선택)",
                    ["yaml", "yml"],
                )
                stt_language = st.selectbox(
                    "STT 언어",
                    options=[code for code, _ in LANGUAGE_OPTIONS],
                    format_func=lambda code: LANGUAGE_LABEL.get(code, code),
                    index=0,
                    key="stt_language_select",
                )
                stt_model = st.selectbox(
                    "모델 크기",
                    options=["tiny", "base", "small", "medium", "large-v3"],
                    index=2, # Default to small
                    key="stt_model_select",
                )
            else:
                st.caption("Gemini 2.5 Flash 설정")
                gemini_translate = st.checkbox("번역 수행 (Translate)", value=True, help="체크 해제 시 전사(Transcription)만 수행합니다.")
                stt_language = "auto" 
                stt_config = None

        stt_async = st.checkbox("비동기 실행", key="stt_async")
        
        if st.button("STT 실행"):
            if "Whisper" in stt_method:
                effective_config = stt_config or str(DEFAULT_STT_CONFIG_PATH)
                override_used = False
                if stt_language != "auto":
                    effective_config = build_override_config(
                        stt_config,
                        DEFAULT_STT_CONFIG_PATH,
                        STT_UI_OVERRIDE_PATH,
                        {
                            "language": stt_language, 
                            "word_timestamps": True,
                            "model_name": stt_model
                        },
                    )
                    override_used = True
                # 모델만 변경된 경우에도 override 적용
                elif stt_model != "small": # small is default in config
                    effective_config = build_override_config(
                        stt_config,
                        DEFAULT_STT_CONFIG_PATH,
                        STT_UI_OVERRIDE_PATH,
                        {
                            "model_name": stt_model,
                            "word_timestamps": True
                        },
                    )
                    override_used = True
                payload = {
                    "input_audio": input_audio,
                    "output_json": stt_output,
                    "config": effective_config,
                }
                endpoint = "stt/"
            else:
                # Gemini Logic
                gemini_config = {
                    "transcribe_only": not gemini_translate,
                    # 한국어 음성을 영어 더빙용으로 사용할 것이므로 기본 번역 대상 언어를 English로 설정
                    "target_language": "English",
                    "source_language": "auto"
                }
                
                # Create temp config
                with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.json', encoding='utf-8') as f:
                    json.dump(gemini_config, f)
                    temp_config_path = f.name
                
                payload = {
                    "input_audio": input_audio,
                    "output_json": stt_output,
                    "config": temp_config_path 
                }
                endpoint = "stt-gemini/"
                override_used = False 

            result = execute_step(endpoint, payload, stt_async)
            
            if result:
                st.session_state["text_process_input_path"] = stt_output
                st.session_state["last_stt_output"] = stt_output  # STT 결과 저장
                st.success("다음 단계(텍스트 처리) 입력이 자동으로 설정되었습니다.")
                
                # 세션 저장
                save_session_data({
                    "stt_input_audio_path": input_audio,
                    "stt_output_path": stt_output,
                    "last_stt_output": stt_output,
                    "last_stt_input_audio": input_audio,
                    "text_process_input_path": stt_output, # 다음 단계 입력 저장
                })

            if override_used:
                cleanup_temp_file(STT_UI_OVERRIDE_PATH)
        
        # 이전 STT 결과가 있으면 항상 표시
        if "last_stt_output" in st.session_state and st.session_state["last_stt_output"]:
            display_stt_result(st.session_state["last_stt_output"])
