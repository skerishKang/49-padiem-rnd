import streamlit as st
from frontend.utils.ui_utils import text_input_with_state
from frontend.utils.api_utils import execute_step
from frontend.constants import DEFAULT_STT_CONFIG_PATH, DEFAULT_TEXT_CONFIG_PATH

def render():
    with st.expander("전체 파이프라인 실행", expanded=True):
        st.write("현재 입력/출력 경로와 설정을 사용해 오디오 추출부터 립싱크까지 순차 실행합니다.")
        pipeline_input = text_input_with_state(
            "입력 미디어 경로",
            "pipeline_input_media",
            st.session_state.get("audio_input_media_path", "data/inputs/source.mp4"),
        )
        pipeline_run = text_input_with_state(
            "실행 결과 기준 폴더",
            "pipeline_run_dir",
            st.session_state.get("run_base_dir", "data/runs/sample"),
        )

        if st.button("전체 파이프라인 실행"):
            step_payloads = [
                (
                    "오디오 추출",
                    "audio/extract",
                    {
                        "input_media": pipeline_input,
                        "output_audio": st.session_state.get("audio_output_path", "data/intermediates/source_audio.wav"),
                        "config": st.session_state.get("audio_config_path"),
                    },
                ),
                (
                    "STT",
                    "stt/",
                    {
                        "input_audio": st.session_state.get("stt_input_audio_path", "data/intermediates/source_audio.wav"),
                        "output_json": st.session_state.get("stt_output_path", "data/intermediates/stt_result.json"),
                        "config": st.session_state.get("stt_config_path", str(DEFAULT_STT_CONFIG_PATH)),
                    },
                ),
                (
                    "텍스트 처리",
                    "text/process",
                    {
                        "input_json": st.session_state.get("text_process_input_path", "data/intermediates/stt_result.json"),
                        "output_json": st.session_state.get("text_process_output_path", "data/intermediates/text_processed.json"),
                        "config": st.session_state.get("text_process_config_path", str(DEFAULT_TEXT_CONFIG_PATH)),
                    },
                ),
                (
                    "VALL-E X",
                    "tts/",
                    {
                        "input_json": st.session_state.get("tts_input_json_path", "data/intermediates/text_processed.json"),
                        "output_audio": st.session_state.get("tts_output_path", "data/intermediates/tts_output.wav"),
                        "config": st.session_state.get("tts_config_path"),
                    },
                ),
                (
                    "RVC",
                    "rvc/",
                    {
                        "input_audio": st.session_state.get("rvc_input_audio_path", "data/intermediates/tts_output.wav"),
                        "output_audio": st.session_state.get("rvc_output_path", "data/intermediates/rvc_output.wav"),
                        "config": st.session_state.get("rvc_config_path"),
                    },
                ),
                (
                    "Wav2Lip",
                    "lipsync/",
                    {
                        "input_video": st.session_state.get("lipsync_input_video_path", pipeline_input),
                        "input_audio": st.session_state.get("lipsync_input_audio_path", "data/intermediates/rvc_output.wav"),
                        "output_video": st.session_state.get("lipsync_output_path", "data/outputs/final_dubbed.mp4"),
                        "config": st.session_state.get("lipsync_config_path"),
                    },
                ),
            ]

            success = True
            for label, endpoint, payload in step_payloads:
                with st.spinner(f"{label} 실행 중..."):
                    result = execute_step(endpoint, payload, async_mode=False)
                if result is None:
                    st.error(f"{label} 단계에서 오류가 발생했습니다. 로그를 확인해 주세요.")
                    success = False
                    break
            if success:
                st.success("전체 파이프라인 실행이 완료되었습니다.")
