import streamlit as st
from pathlib import Path
import json
import tempfile
from frontend_unified.utils.ui_utils import handle_file_input, text_input_with_state
from frontend_unified.utils.api_utils import execute_step
from frontend_unified.utils.config_utils import update_output_path_from_input, save_session_data
from frontend_unified.utils.i18n import get_text

def render():
    with st.expander("TTS (Text-to-Speech)", expanded=True):
        st.write("텍스트를 음성으로 변환합니다.")
        
        tts_method = st.radio(
            get_text("tts_method_select"),
            [get_text("tts_vallex"), get_text("tts_gemini")],
            index=0,
            horizontal=True
        )

        col_input, col_config = st.columns([2, 1])

        with col_input:
            # 텍스트 처리 단계에서 설정한 TTS 입력 JSON 경로를 기본값으로 사용
            default_tts_input = st.session_state.get("tts_input_json_path", "data/intermediates/text_process_result.json")
            tts_input = handle_file_input(
                "TTS 입력 JSON 경로",
                "tts_input_json_path",
                default_tts_input,
                "TTS 입력 JSON 업로드",
                ["json"],
            )

            # 입력 경로 기반 출력 경로 자동 업데이트
            # Gemini TTS도 실제 응답은 WAV 포맷이므로 확장자를 .wav로 통일
            update_output_path_from_input(tts_input, "tts_output_path", "_valle.wav" if "VALL-E X" in tts_method else "_gemini.wav")
        
            # update_run_defaults 또는 위에서 계산한 출력 경로를 기본값으로 사용
            default_tts_output = st.session_state.get(
                "tts_output_path",
                "data/intermediates/tts_output.wav",
            )
            tts_output = text_input_with_state(
                "TTS 출력 오디오 경로",
                "tts_output_path",
                default_tts_output,
            )

        with col_config:
            if "VALL-E X" in tts_method:
                tts_config = handle_file_input(
                    "TTS 설정 파일 경로",
                    "tts_config",
                    "modules/tts_vallex/config/settings.yaml",
                    "TTS 설정 업로드(선택)",
                    ["yaml", "yml", "json"],
                )
            else:
                st.caption("Gemini 2.5 Flash TTS 설정")

                # gemini-dub-live-interpret/types.ts 의 VOICE_OPTIONS 를 반영한 음성 목록
                #  - Puck   (Male, Deep/Calm)
                #  - Charon (Male, Deep/Authority)
                #  - Kore   (Female, Calm/Soothing)
                #  - Fenrir (Male, Deep/Growly)
                #  - Zephyr (Female, High/Energetic)
                gemini_voice_labels = {
                    "Puck": "Puck (남 / 저음 · 차분)",
                    "Charon": "Charon (남 / 저음 · 권위 있는 톤)",
                    "Kore": "Kore (여 / 차분 · 부드러운 톤)",
                    "Fenrir": "Fenrir (남 / 저음 · 거친 톤)",
                    "Zephyr": "Zephyr (여 / 고음 · 에너제틱)",
                }
                gemini_voice = st.selectbox(
                    "Gemini 음성 선택",
                    options=list(gemini_voice_labels.keys()),
                    index=0,
                    format_func=lambda name: gemini_voice_labels.get(name, name),
                    key="tts_gemini_voice_select",
                    help="원하는 성별/톤을 가진 Gemini 음성을 선택하세요.",
                )
                # 실제 config 파일 경로는 버튼 클릭 시에 임시 JSON으로 생성
                tts_config = None

        tts_async = st.checkbox("비동기 실행", key="tts_async")
        
        if st.button("음성 합성 실행"):
            # 기본 config 값 (VALL-E X 는 설정 파일 경로 그대로 사용)
            config_value = tts_config or None

            if "VALL-E X" in tts_method:
                endpoint = "tts/"
            else:
                # Gemini TTS: 선택된 음성을 config JSON에 담아서 임시 파일로 저장
                voice_name = st.session_state.get("tts_gemini_voice_select", "Puck")
                gemini_cfg = {"voice_name": voice_name}
                with tempfile.NamedTemporaryFile(mode="w", delete=False, suffix=".json", encoding="utf-8") as f:
                    json.dump(gemini_cfg, f)
                    config_value = f.name
                endpoint = "tts-gemini/"

            payload = {
                "input_json": tts_input,
                "output_audio": tts_output,
                "config": config_value,
            }
                
            result = execute_step(endpoint, payload, tts_async)
            
            if result:
                # 실행이 성공하면 최근 TTS 출력 경로만 업데이트하고,
                # 실제 플레이어는 하단 "최근 TTS 출력" 섹션에서 한 번만 노출한다.
                st.session_state["last_tts_output"] = tts_output
                st.session_state["rvc_input_audio_path"] = tts_output
                st.session_state["lipsync_input_audio_path"] = tts_output
                st.success("다음 단계(RVC/립싱크) 입력이 자동으로 설정되었습니다.")

                # 세션 저장
                save_session_data({
                    "tts_input_json_path": tts_input,
                    "tts_output_path": tts_output,
                    "last_tts_output": tts_output,
                    "rvc_input_audio_path": tts_output, # 다음 단계 입력 저장
                    "lipsync_input_audio_path": tts_output,
                })
            else:
                # 요청이 실패했더라도 파일이 생성되었다면 재생할 수 있게 안내
                if Path(tts_output).exists():
                    st.warning("API 응답은 실패했지만 출력 파일이 생성되었습니다. 아래에서 재생할 수 있습니다.")
                    st.session_state["last_tts_output"] = tts_output
                    save_session_data({"last_tts_output": tts_output})

        # 최근 TTS 출력이 있으면 항상 재생 가능하게 노출
        last_tts_out = st.session_state.get("last_tts_output")
        if last_tts_out and Path(last_tts_out).exists():
            st.caption("최근 TTS 출력")
            st.audio(last_tts_out)
