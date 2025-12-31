import streamlit as st
from frontend.utils.ui_utils import handle_file_input, text_input_with_state
from frontend.utils.api_utils import execute_step
from frontend.utils.config_utils import update_output_path_from_input, save_session_data

def render():
    with st.expander("Wav2Lip 립싱크", expanded=True):
        st.write("변환된 음성을 영상에 립싱크로 합성합니다.")
        col_input, col_config = st.columns([2, 1])

        with col_input:
            lipsync_video = handle_file_input(
                "립싱크 입력 영상 경로",
                "lipsync_input_video",
                "data/inputs/source.mp4",
                "립싱크 입력 영상 업로드",
                ["mp4", "mov", "avi"],
            )

            lipsync_audio = handle_file_input(
                "립싱크 입력 오디오 경로",
                "lipsync_input_audio",
                "data/intermediates/rvc_output.wav",
                "립싱크 오디오 업로드",
                ["wav", "mp3", "flac", "m4a"],
            )
            
            # 입력 경로 기반 출력 경로 자동 업데이트 (오디오 경로 기준)
            update_output_path_from_input(lipsync_audio, "lipsync_output_path", "_wav2lip.mp4")
            lipsync_output = text_input_with_state(
                "립싱크 출력 영상 경로",
                "lipsync_output_path",
                "data/outputs/final_dubbed.mp4",
            )

        with col_config:
            lipsync_config = handle_file_input(
                "립싱크 설정 파일 경로",
                "lipsync_config",
                "",
                "립싱크 설정 업로드(선택)",
                ["yaml", "yml", "json"],
            )
        lipsync_async = st.checkbox("비동기 실행", key="lipsync_async")
        if st.button("립싱크 실행"):
            payload = {
                "input_video": lipsync_video,
                "input_audio": lipsync_audio,
                "output_video": lipsync_output,
                "config": lipsync_config or None,
            }
            result = execute_step("lipsync/", payload, lipsync_async)
            if result:
                st.video(lipsync_output)
                
                # 세션 저장
                save_session_data({
                    "lipsync_input_video_path": lipsync_video,
                    "lipsync_input_audio_path": lipsync_audio,
                    "lipsync_output_path": lipsync_output,
                })
