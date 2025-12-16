import streamlit as st
from pathlib import Path
from frontend.utils.ui_utils import handle_file_input, text_input_with_state
from frontend.utils.api_utils import execute_step
from frontend.utils.config_utils import update_run_defaults, save_session_data

def render():
    with st.expander("오디오 추출", expanded=True):
        st.write("동영상/미디어에서 오디오를 추출합니다.")
        col_input, col_config = st.columns([2, 1])

        with col_input:
            st.markdown("**입력 미디어 (영상/음성 파일)**")
            input_media = handle_file_input(
                "입력 미디어 경로",
                "audio_input_media_path",
                "data/inputs/source.mp4",
                "입력 미디어 업로드",
                ["mp4", "mov", "mkv", "avi", "mp3", "wav", "m4a", "aac", "flac", "ogg"],
            )
            
            # 초기화 및 변경 감지: 입력이 처음 설정되었거나 바뀌었을 때마다 기본 경로들을 갱신
            if "last_audio_input_media" not in st.session_state or input_media != st.session_state.get("last_audio_input_media"):
                update_run_defaults(input_media)
                st.session_state["last_audio_input_media"] = input_media
                
            if run_dir := st.session_state.get("run_base_dir"):
                st.caption(f"현재 실행 폴더: {run_dir}")
            # update_run_defaults 에서 설정한 audio_output_path를 기본값으로 사용
            default_audio_output = st.session_state.get("audio_output_path", "data/intermediates/source_audio.wav")
            output_audio = text_input_with_state(
                "출력 오디오 경로",
                "audio_output_path",
                default_audio_output,
            )

        with col_config:
            st.markdown("**설정 파일 (YAML만 허용)**")
            st.caption("필요 시 ffmpeg 경로, 코덱 등을 지정합니다. 음성 파일은 왼쪽 영역에서 업로드하세요.")
            config_path = handle_file_input(
                "설정 파일 경로",
                "audio_config",
                "",
                "설정 파일 업로드(선택)",
                ["yaml", "yml"],
            )

        audio_async = st.checkbox("비동기 실행", key="audio_async")
        if st.button("오디오 추출 실행"):
            payload = {
                "input_media": input_media,
                "output_audio": output_audio,
                "config": config_path or None,
            }
            result = execute_step("audio/extract", payload, audio_async)
            if result:
                st.audio(output_audio)
                st.session_state["stt_input_audio_path"] = output_audio
                st.success("다음 단계(STT) 입력이 자동으로 설정되었습니다.")
                
                # 세션 저장 (파일 경로 기억)
                session_data = {
                    "audio_input_media_path": input_media,
                    "audio_output_path": output_audio,
                    "current_run_name": st.session_state.get("current_run_name"),
                    "run_base_dir": st.session_state.get("run_base_dir"),
                    "last_audio_input_media": input_media,
                }
                
                # 입력이 비디오라면 립싱크 입력 비디오 경로도 즉시 업데이트 (UI 반영을 위해 widget key도 업데이트)
                if Path(input_media).suffix.lower() in [".mp4", ".mov", ".avi", ".mkv"]:
                    session_data["lipsync_input_video_path"] = input_media
                    st.session_state["lipsync_input_video_path"] = input_media
                    st.session_state["lipsync_input_video_path_text"] = input_media # 위젯 강제 업데이트
                    
                save_session_data(session_data)
