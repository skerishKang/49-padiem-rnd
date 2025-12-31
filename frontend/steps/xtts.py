import streamlit as st
from pathlib import Path
from frontend.utils.ui_utils import handle_file_input, text_input_with_state
from frontend.utils.api_utils import execute_step
from frontend.utils.config_utils import update_output_path_from_input, save_session_data

def render():
    with st.expander("XTTS 백업 합성", expanded=True):
        st.write("백업 TTS 경로를 통해 음성을 합성합니다.")
        col_input, col_config = st.columns([2, 1])

        with col_input:
            xtts_input = handle_file_input(
                "XTTS 입력 JSON 경로",
                "xtts_input_json",
                "data/intermediates/text_process_result.json",
                "XTTS 입력 JSON 업로드",
                ["json"],
            )

            # 입력 경로 기반 출력 경로 자동 업데이트
            update_output_path_from_input(xtts_input, "xtts_output_path", "_xtts.wav")

            xtts_output = text_input_with_state(
                "XTTS 출력 WAV 경로",
                "xtts_output_path",
                "data/intermediates/tts_backup_output.wav",
            )

        with col_config:
            xtts_config = handle_file_input(
                "XTTS 설정 파일 경로",
                "xtts_config",
                "modules/tts_xtts/config/settings.yaml",
                "XTTS 설정 업로드(선택)",
                ["yaml", "yml", "json"],
            )
            
            # 기본 스피커 오디오를 원본 입력 오디오로 설정
            default_speaker = st.session_state.get("stt_input_audio_path", "data/inputs/test_audio.wav")
            
            xtts_speaker = handle_file_input(
                "스피커 참조 오디오 (필수)",
                "xtts_speaker_wav",
                default_speaker,
                "스피커 오디오 업로드",
                ["wav", "mp3"],
            )
            
            xtts_lang = st.selectbox(
                "언어 설정 (자동 감지 또는 선택)",
                ["ko", "en", "ja", "zh-cn", "auto"],
                index=4,
                help="텍스트의 언어와 일치시켜주세요. 'auto'는 텍스트 내용을 기반으로 추론합니다."
            )
        xtts_async = st.checkbox("비동기 실행", key="xtts_async")
        if st.button("XTTS 합성 실행"):
            payload = {
                "input_json": xtts_input,
                "output_audio": xtts_output,
                "config": xtts_config or None,
                "speaker_wav": xtts_speaker or None,
                "language": xtts_lang if xtts_lang != "auto" else None,
            }
            result = execute_step("tts-backup/", payload, xtts_async)
            if result:
                # st.audio(xtts_output) # 중복 플레이어 제거 (아래 persistent player 사용)
                st.session_state["rvc_input_audio_path"] = xtts_output
                st.session_state["lipsync_input_audio"] = xtts_output
                # st.success("다음 단계(RVC) 입력이 자동으로 설정되었습니다.") # 사용자 요청으로 제거
                
                # 세션 저장
                save_session_data({
                    "xtts_input_json_path": xtts_input,
                    "xtts_output_path": xtts_output,
                    "rvc_input_audio_path": xtts_output, # 다음 단계 입력 저장
                    "last_xtts_output": xtts_output, # 최근 출력 저장
                    "lipsync_input_audio": xtts_output,
                })
                st.session_state["last_xtts_output"] = xtts_output

        # 최근 XTTS 출력이 있으면 항상 재생 가능하게 노출
        last_xtts_out = st.session_state.get("last_xtts_output")
        if last_xtts_out and Path(last_xtts_out).exists():
            st.caption("최근 XTTS 출력")
            st.audio(last_xtts_out)
