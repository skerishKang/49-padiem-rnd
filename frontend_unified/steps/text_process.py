import streamlit as st
import os
from frontend.utils.ui_utils import handle_file_input, text_input_with_state, display_text_summary
from frontend.utils.api_utils import execute_step
from frontend.utils.config_utils import update_output_path_from_input, save_session_data
from frontend.constants import DEFAULT_TEXT_CONFIG_PATH

def render():
    with st.expander("텍스트 처리/번역", expanded=True):
        st.write("STT 결과를 전처리하거나 번역합니다.")
        col_input, col_config = st.columns([2, 1])

        with col_input:
            st.markdown("**입력/출력 JSON**")
            # STT 단계에서 설정한 텍스트 입력 경로를 기본값으로 사용
            default_text_input = st.session_state.get("text_process_input_path", "data/intermediates/source_audio_result.json")
            input_json = handle_file_input(
                "텍스트 처리 입력 JSON 경로",
                "text_process_input_path",
                default_text_input,
                "텍스트 처리 입력 JSON 업로드",
                ["json"],
            )
            
            # 입력 경로 기반 출력 경로 자동 업데이트
            update_output_path_from_input(input_json, "text_process_output_path", "_text.json")
            
            # update_run_defaults 또는 위에서 계산한 출력 경로를 기본값으로 사용
            default_text_output = st.session_state.get("text_process_output_path", "data/intermediates/text_process_result.json")
            text_output = text_input_with_state(
                "텍스트 처리 결과 JSON 경로",
                "text_process_output_path",
                default_text_output,
            )

        with col_config:
            st.markdown("**설정**")
            st.caption("번역할 언어와 Gemini API 키를 설정하세요.")
            
            text_config = handle_file_input(
                "텍스트 처리 설정 파일 경로",
                "text_config",
                str(DEFAULT_TEXT_CONFIG_PATH),
                "텍스트 설정 업로드(선택)",
                ["yaml", "yml"],
            )
            
            source_lang = st.selectbox("원본 언어", ["한국어", "영어", "일본어", "중국어", "자동"], index=4)
            target_lang = st.selectbox("번역 언어", ["영어", "한국어", "일본어", "중국어"], index=0)

            # 환경변수에 Gemini 키가 있으면 자동으로 사용하고, 없을 때만 직접 입력받음
            gemini_api_key_env = os.getenv("GEMINI_API_KEY")
            if gemini_api_key_env:
                st.caption("Gemini API Key는 환경변수 GEMINI_API_KEY 값을 자동으로 사용합니다.")
                # env를 사용할 것이므로 백엔드에는 별도 키를 전달하지 않음
                gemini_api_key = None
            else:
                gemini_api_key = st.text_input(
                    "Gemini API Key", 
                    type="password", 
                    value="",
                    help="번역을 위해 필요합니다."
                )

            lang_map = {"한국어": "ko", "영어": "en", "일본어": "ja", "중국어": "zh", "자동": "auto"}
            
            syllable_tolerance = st.slider("허용 음절 비율 (±)", 0.05, 0.30, 0.10, 0.05)
            enforce_timing = st.checkbox("타이밍 엄격 모드", value=True)

        text_async = st.checkbox("비동기 실행", key="text_async")
        if st.button("텍스트 처리 실행"):
            payload = {
                "input_json": input_json,
                "output_json": text_output,
                "config": text_config or None,
                "source_language": lang_map[source_lang],
                "target_language": lang_map[target_lang],
                "syllable_tolerance": syllable_tolerance,
                "enforce_timing": enforce_timing,
                "gemini_api_key": gemini_api_key,
            }
            result = execute_step("text/process", payload, text_async)
            if result:
                st.session_state["tts_input_json_path"] = text_output
                st.session_state["xtts_input_json_path"] = text_output
                st.session_state["last_text_output"] = text_output  # 결과 저장
                st.success("다음 단계(TTS) 입력이 자동으로 설정되었습니다.")

                # 세션 저장
                save_session_data({
                    "text_process_input_path": input_json,
                    "text_process_output_path": text_output,
                    "last_text_output": text_output,
                    "tts_input_json_path": text_output, # 다음 단계 입력 저장
                    "xtts_input_json_path": text_output, # 다음 단계 입력 저장
                })
        
        # 이전 결과가 있으면 항상 표시
        if "last_text_output" in st.session_state and st.session_state["last_text_output"]:
            st.subheader("텍스트 처리 요약")
            display_text_summary(st.session_state["last_text_output"])
