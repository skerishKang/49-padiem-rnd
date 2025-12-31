import streamlit as st
from pathlib import Path
from frontend.utils.ui_utils import handle_file_input, text_input_with_state
from frontend.utils.api_utils import execute_step
from frontend.utils.config_utils import update_output_path_from_input, save_session_data

def render():
    with st.expander("VALL-E X 합성", expanded=True):
        st.write("전처리된 텍스트를 기반으로 음성을 합성합니다.")
        col_input, col_config = st.columns([2, 1])

        with col_input:
            tts_input = handle_file_input(
                "TTS 입력 JSON 경로",
                "tts_input_json",
                "data/intermediates/text_process_result.json",
                "TTS 입력 JSON 업로드",
                ["json"],
            )

            # 입력 경로 기반 출력 경로 자동 업데이트
            update_output_path_from_input(tts_input, "tts_output_path", "_valle.wav")

            tts_output = text_input_with_state(
                "TTS 출력 WAV 경로",
                "tts_output_path",
                "data/intermediates/tts_output.wav",
            )

        with col_config:
            tts_config = handle_file_input(
                "TTS 설정 파일 경로",
                "tts_config",
                "modules/tts_vallex/config/settings.yaml",
                "TTS 설정 업로드(선택)",
                ["yaml", "yml", "json"],
            )

        tts_async = st.checkbox("비동기 실행", key="tts_async")
        if st.button("VALL-E X 합성 실행"):
            payload = {
                "input_json": tts_input,
                "output_audio": tts_output,
                "config": tts_config or None,
            }
            result = execute_step("tts/", payload, tts_async)
            if result:
                st.audio(tts_output)
                st.session_state["last_tts_output"] = tts_output
                st.session_state["rvc_input_audio_path"] = tts_output
                st.session_state["lipsync_input_audio"] = tts_output
                st.success("다음 단계(RVC/립싱크) 입력이 자동으로 설정되었습니다.")

                # 세션 저장
                save_session_data({
                    "tts_input_json_path": tts_input,
                    "tts_output_path": tts_output,
                    "last_tts_output": tts_output,
                    "rvc_input_audio_path": tts_output, # 다음 단계 입력 저장
                    "lipsync_input_audio": tts_output,
                })
            else:
                # 요청이 실패했더라도 파일이 생성되었다면 재생할 수 있게 안내
                if Path(tts_output).exists():
                    st.warning("API 응답은 실패했지만 출력 파일이 생성되었습니다. 아래에서 재생하세요.")
                    st.audio(tts_output)
                    st.session_state["last_tts_output"] = tts_output
                    save_session_data({"last_tts_output": tts_output})

        # 최근 VALL-E X 출력이 있으면 항상 재생 가능하게 노출
        last_tts_out = st.session_state.get("last_tts_output")
        if last_tts_out and Path(last_tts_out).exists():
            st.caption("최근 VALL-E X 출력")
            st.audio(last_tts_out)
