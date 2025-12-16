import streamlit as st
from frontend_unified.utils.ui_utils import handle_file_input, text_input_with_state
from frontend_unified.utils.api_utils import execute_step
from frontend_unified.utils.config_utils import update_output_path_from_input, save_session_data
from frontend_unified.utils.rvc_automation import apply_latest_model


def render():
    with st.expander("RVC 음성 변환", expanded=True):
        st.write("합성된 음성을 타깃 화자의 음색으로 변환합니다.")
        col_input, col_config = st.columns([2, 1])

        with col_input:
            default_rvc_input = st.session_state.get("rvc_input_audio_path", "data/intermediates/tts_output.wav")
            rvc_input = handle_file_input(
                "RVC 입력 WAV 경로",
                "rvc_input_audio_path",
                default_rvc_input,
                "RVC 입력 오디오 업로드",
                ["wav", "mp3"],
            )

            # 입력 경로 기반 출력 경로 자동 업데이트
            update_output_path_from_input(rvc_input, "rvc_output_path", "_rvc.wav")

            default_rvc_output = st.session_state.get("rvc_output_path", "data/intermediates/rvc_output.wav")
            rvc_output = text_input_with_state(
                "RVC 출력 WAV 경로",
                "rvc_output_path",
                default_rvc_output,
            )

        with col_config:
            rvc_config = handle_file_input(
                "RVC 설정 파일 경로",
                "rvc_config",
                "modules/voice_conversion_rvc/config/settings.yaml",
                "RVC 설정 업로드(선택)",
                ["yaml", "yml", "json"],
            )
            
            st.markdown("---")
            st.caption("RVC 모델 학습 및 적용")
            
            col_rvc_btns = st.columns(2)
            with col_rvc_btns[0]:
                if st.button("RVC WebUI 열기", help="모델 학습을 위한 웹 인터페이스를 엽니다."):
                    # RVC WebUI가 로컬 7865 포트에서 실행 중이라고 가정
                    js = "window.open('http://127.0.0.1:7865', '_blank')"
                    st.components.v1.html(f"<script>{js}</script>", height=0)
                    st.info("브라우저 팝업이 차단되었다면 허용해주세요. (http://127.0.0.1:7865)")
            
            with col_rvc_btns[1]:
                if st.button("최신 모델 자동 적용", help="가장 최근에 학습된 모델을 찾아 설정에 적용합니다."):
                    success, msg = apply_latest_model()
                    if success:
                        st.success(msg)
                        # Force reload config path to ensure UI updates if needed (though file input might need manual refresh)
                    else:
                        st.error(msg)
            
            st.info("""
            **수동 설정 방법**
            1. **RVC WebUI**에서 모델 학습 완료
            2. `.pth` 파일을 `modules/voice_conversion_rvc/checkpoints/`에 이동
            3. `settings.yaml`의 `checkpoint` 경로 수정
            (자동 적용 버튼을 누르면 2, 3번이 자동으로 수행됩니다.)
            """)
        rvc_async = st.checkbox("비동기 실행", key="rvc_async")
        if st.button("RVC 변환 실행"):
            payload = {
                "input_audio": rvc_input,
                "output_audio": rvc_output,
                "config": rvc_config or None,
            }
            result = execute_step("rvc/", payload, rvc_async)
            if result:
                st.audio(rvc_output)
                st.session_state["lipsync_input_audio_path"] = rvc_output
                st.success("다음 단계(립싱크) 입력이 자동으로 설정되었습니다.")

                # 세션 저장
                save_session_data({
                    "rvc_input_audio_path": rvc_input,
                    "rvc_output_path": rvc_output,
                    "lipsync_input_audio_path": rvc_output, # 다음 단계 입력 저장
                })
