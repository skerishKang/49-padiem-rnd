import streamlit as st
from pathlib import Path
from frontend.utils.ui_utils import handle_file_input, text_input_with_state
from frontend.utils.api_utils import execute_step
from frontend.utils.config_utils import update_output_path_from_input, save_session_data

def render():
    with st.expander("Wav2Lip 립싱크", expanded=True):
        st.write("변환된 음성을 영상에 립싱크로 합성합니다.")
        col_input, col_config = st.columns([2, 1])

        with col_input:
            # 기본 비디오 경로 설정 (source.mp4가 없으면 다른 mp4 파일 검색)
            default_video_path = "data/inputs/source.mp4"
            if not Path(default_video_path).exists():
                input_dir = Path("data/inputs")
                if input_dir.exists():
                    mp4_files = list(input_dir.glob("*.mp4"))
                    if mp4_files:
                        default_video_path = str(mp4_files[0])

            default_lipsync_video = st.session_state.get("lipsync_input_video_path", default_video_path)
            
            lipsync_video = handle_file_input(
                "립싱크 입력 영상 경로",
                "lipsync_input_video_path",
                default_lipsync_video,
                "립싱크 입력 영상 업로드",
                ["mp4", "mov", "avi"],
            )
            
            # 입력 경로 기반 출력 경로 자동 업데이트 (입력 영상 stem + '_dubbed.mp4')
            # update_output_path_from_input(lipsync_video, "lipsync_output_path", "_dubbed.mp4")

            # 오디오 소스 빠른 선택 (Gemini, XTTS, RVC 등 결과물 자동 탐색)
            run_dir = st.session_state.get("run_base_dir", "data/runs/sample")
            intermediates_dir = Path(run_dir) / "intermediates"
            
            candidate_audios = []
            if intermediates_dir.exists():
                # 주요 오디오 패턴 검색
                patterns = ["*_gemini.wav", "*_valle.wav", "*_xtts.wav", "*_rvc.wav"]
                for pat in patterns:
                    found = list(intermediates_dir.glob(pat))
                    candidate_audios.extend(found)
                
                # 중복 제거 및 정렬 (최신 수정순)
                candidate_audios = sorted(list(set(candidate_audios)), key=lambda x: x.stat().st_mtime, reverse=True)

            if candidate_audios:
                st.markdown("**오디오 소스 빠른 변경**")
                selected_candidate = st.selectbox(
                    "감지된 오디오 파일 목록 (선택 시 아래 경로가 변경됩니다)",
                    options=["선택하세요..."] + [str(p) for p in candidate_audios],
                    format_func=lambda x: Path(x).name if x != "선택하세요..." else x,
                    key="lipsync_audio_candidate_select"
                )
                
                if selected_candidate != "선택하세요...":
                    # 선택 시 세션 및 위젯 강제 업데이트
                    st.session_state["lipsync_input_audio_path"] = selected_candidate
                    st.session_state["lipsync_input_audio_path_text"] = selected_candidate

            default_lipsync_audio = st.session_state.get("lipsync_input_audio_path", "data/intermediates/rvc_output.wav")
            lipsync_audio = handle_file_input(
                "립싱크 입력 오디오 경로",
                "lipsync_input_audio_path",
                default_lipsync_audio,
                "립싱크 오디오 업로드",
                ["wav", "mp3", "flac", "m4a"],
            )

            # 입력 경로 기반 출력 경로 자동 업데이트 (오디오 경로 기준)
            update_output_path_from_input(lipsync_audio, "lipsync_output_path", "_dubbed.mp4")
            default_lipsync_output = st.session_state.get("lipsync_output_path", "data/outputs/final_dubbed.mp4")
            lipsync_output = text_input_with_state(
                "립싱크 출력 영상 경로",
                "lipsync_output_path",
                default_lipsync_output,
            )

        with col_config:
            default_config_path = "modules/lipsync_wav2lip/config/settings.yaml"
            # 세션에 값이 없거나 비어있으면 기본값으로 강제 설정
            if not st.session_state.get("lipsync_config"):
                st.session_state["lipsync_config"] = default_config_path

            lipsync_config = handle_file_input(
                "립싱크 설정 파일 경로",
                "lipsync_config",
                default_config_path,
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
