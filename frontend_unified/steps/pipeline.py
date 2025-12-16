import streamlit as st
import os
from pathlib import Path
import tempfile
import json
from frontend_unified.utils.ui_utils import text_input_with_state
from frontend_unified.utils.api_utils import execute_step
from frontend_unified.utils.config_utils import update_run_defaults
from frontend_unified.constants import (
    DEFAULT_STT_CONFIG_PATH,
    DEFAULT_TEXT_CONFIG_PATH,
    DEFAULT_TTS_VALLEX_CONFIG_PATH,
    DEFAULT_LIPSYNC_CONFIG_PATH,
)
from frontend_unified.utils.i18n import get_text

def render():
    st.markdown("### 전체 파이프라인 실행")
    with st.expander(get_text("full_pipeline_title"), expanded=True):
        st.write(get_text("full_pipeline_desc"))
        
        # 1. 파일 선택 (Dropdown + Upload)
        input_dir = Path("data/inputs")
        if not input_dir.exists():
            input_dir.mkdir(parents=True, exist_ok=True)
            
        # File Upload
        uploaded_file = st.file_uploader("입력 미디어 업로드 (Upload Input Media)", type=["mp4", "mp3", "wav", "m4a"])
        if uploaded_file:
            file_path = input_dir / uploaded_file.name
            with open(file_path, "wb") as f:
                f.write(uploaded_file.getbuffer())
            st.success(f"파일 업로드 완료: {uploaded_file.name}")

        input_files = [f.name for f in input_dir.glob("*") if f.is_file()]
        
        selected_file = None
        if not input_files:
            st.warning("data/inputs 폴더에 파일이 없습니다. 파일을 업로드해주세요.")
            pipeline_input = ""
        else:
            # If uploaded, set index to that file
            index = 0
            if uploaded_file and uploaded_file.name in input_files:
                index = input_files.index(uploaded_file.name)
                
            selected_file = st.selectbox(
                get_text("input_media_select"),
                input_files,
                index=index
            )
            pipeline_input = str(input_dir / selected_file) if selected_file else ""
            st.caption(f"{get_text('input_label')}{pipeline_input}")

        pipeline_run = text_input_with_state(
            get_text("run_base_dir"),
            "pipeline_run_dir",
            st.session_state.get("run_base_dir", "data/runs/sample"),
        )

        # 2. 모델 선택 (Method Selection)
        st.markdown("#### 모델 선택 (Model Selection)")
        col_methods = st.columns(3)
        with col_methods[0]:
            stt_method = st.radio("STT 모델", ["Whisper (Local)", "Gemini (Cloud)"], index=0)
        with col_methods[1]:
            tts_method = st.radio("TTS 모델", ["VALL-E X (Local)", "XTTS (Local)", "Gemini (Cloud)"], index=0)
        with col_methods[2]:
            lipsync_method = st.radio("LipSync 모델", ["Wav2Lip (Standard)", "MuseTalk (High-Res)"], index=0)
            
        target_lang = st.selectbox(
            "목표 언어 (Target Language)",
            ["Korean", "English", "Japanese", "Chinese", "Spanish", "French", "German"],
            index=1, # Default to English
            help="STT 단계에서 번역할 목표 언어를 선택하세요."
        )

        # 3. 단계 선택 (Checkboxes)
        st.markdown(get_text("select_steps"))
        
        # Auto-skip LipSync logic
        disable_lipsync = False
        lipsync_value = True
        if selected_file:
            ext = Path(selected_file).suffix.lower()
            if ext in [".mp3", ".wav", ".m4a", ".flac", ".aac"]:
                disable_lipsync = True
                lipsync_value = False
                st.info("ℹ️ 오디오 파일이 감지되어 립싱크 단계가 자동으로 해제되었습니다.")

        col_steps = st.columns(5)
        with col_steps[0]:
            run_stt = st.checkbox(get_text("step_stt"), value=True)
        with col_steps[1]:
            run_text = st.checkbox(get_text("step_text"), value=True)
        with col_steps[2]:
            run_tts = st.checkbox(get_text("step_tts"), value=True)
        with col_steps[3]:
            run_rvc = st.checkbox(get_text("step_rvc"), value=True)
        with col_steps[4]:
            run_lipsync = st.checkbox(get_text("step_lipsync"), value=lipsync_value, disabled=disable_lipsync)

        if st.button(get_text("run_selected_steps")):
            if not pipeline_input:
                st.error("입력 파일을 선택해주세요.")
            else:
                # 실행 전에 입력 파일 기준으로 기본 경로들을 갱신
                update_run_defaults(pipeline_input)

                # TTS 모델에 따라 출력 경로(파일명) 조정
                base_dir = Path(st.session_state.get("run_base_dir", "data/runs/sample"))
                intermediates_dir = base_dir / "intermediates"
                input_stem = Path(pipeline_input).stem
                
                if "Gemini" in tts_method:
                    tts_output = str(intermediates_dir / f"{input_stem}_gemini.wav")
                elif "XTTS" in tts_method:
                    tts_output = str(intermediates_dir / f"{input_stem}_xtts.wav")
                else:
                    tts_output = str(intermediates_dir / f"{input_stem}_valle.wav")
                
                # 세션 상태 업데이트 (다른 단계에서 참조할 수 있도록)
                st.session_state["tts_output_path"] = tts_output

                audio_output = st.session_state.get("audio_output_path", "data/intermediates/source_audio.wav")
                stt_input_audio = st.session_state.get("stt_input_audio_path", audio_output)
                stt_output = st.session_state.get("stt_output_path", "data/intermediates/stt_result.json")
                text_input_json = st.session_state.get("text_process_input_path", stt_output)
                text_output_json = st.session_state.get("text_process_output_path", "data/intermediates/text_processed.json")
                tts_input_json = st.session_state.get("tts_input_json_path", text_output_json)
                # tts_output is already set above
                rvc_input_audio = st.session_state.get("rvc_input_audio_path", tts_output)
                rvc_output = st.session_state.get("rvc_output_path", "data/intermediates/rvc_output.wav")
                lipsync_input_video = st.session_state.get("lipsync_input_video_path", pipeline_input)
                lipsync_input_audio = st.session_state.get("lipsync_input_audio_path", rvc_output)
                lipsync_output = st.session_state.get("lipsync_output_path", "data/outputs/final_dubbed.mp4")

                # RVC 단계를 실행하지 않는 경우, 립싱크 입력 오디오는 RVC 출력이 아닌
                # TTS 출력 오디오(rvc_input_audio)를 그대로 사용하도록 보정한다.
                if not run_rvc:
                    lipsync_input_audio = tts_output
                    st.session_state["lipsync_input_audio_path"] = lipsync_input_audio

                step_payloads = []
                
                # 1. Audio Extraction
                if run_stt:
                    step_payloads.append((
                        "오디오 추출",
                        "audio/extract",
                        {
                            "input_media": pipeline_input,
                            "output_audio": audio_output,
                            "config": None,
                        },
                    ))
                    
                    # STT Method Logic
                    if "Gemini" in stt_method:
                        # Gemini STT
                        # Create temp config for target language
                        stt_config_data = {
                            "target_language": target_lang,
                            "source_language": "auto",
                            "transcribe_only": False
                        }
                        
                        # Use a fixed temp file path or create one
                        # Since we can't easily manage temp file lifecycle across requests in this simple script,
                        # we'll create a file in the temp directory.
                        temp_config_path = Path("temp") / "stt_gemini_config.json"
                        temp_config_path.parent.mkdir(parents=True, exist_ok=True)
                        with open(temp_config_path, "w", encoding="utf-8") as f:
                            json.dump(stt_config_data, f)

                        step_payloads.append((
                            "STT (Gemini)",
                            "stt-gemini/", 
                            {
                                "input_audio": stt_input_audio,
                                "output_json": stt_output,
                                "config": str(temp_config_path)
                            },
                        ))
                    else:
                        # Whisper STT
                        step_payloads.append((
                            "STT (Whisper)",
                            "stt/", 
                            {
                                "input_audio": stt_input_audio,
                                "output_json": stt_output,
                                "config": str(DEFAULT_STT_CONFIG_PATH),
                            },
                        ))

                if run_text:
                    step_payloads.append((
                        "텍스트 처리",
                        "text/process",
                        {
                            "input_json": text_input_json,
                            "output_json": text_output_json,
                            "config": str(DEFAULT_TEXT_CONFIG_PATH),
                        },
                    ))

                if run_tts:
                    # TTS Method Logic
                    if "Gemini" in tts_method:
                        step_payloads.append((
                            "TTS (Gemini)",
                            "tts-gemini/",
                            {
                                "input_json": tts_input_json,
                                "output_audio": tts_output,
                                "config": None,
                            },
                        ))
                    elif "XTTS" in tts_method:
                        step_payloads.append((
                            "TTS (XTTS)",
                            "tts-backup/",
                            {
                                "input_json": tts_input_json,
                                "output_audio": tts_output,
                                "config": None,
                            },
                        ))
                    else:
                        # VALL-E X
                        step_payloads.append((
                            "TTS (VALL-E X)",
                            "tts/", 
                            {
                                "input_json": tts_input_json,
                                "output_audio": tts_output,
                                "config": str(DEFAULT_TTS_VALLEX_CONFIG_PATH),
                            },
                        ))

                if run_rvc:
                    step_payloads.append((
                        "RVC 변환",
                        "rvc/",
                        {
                            "input_audio": rvc_input_audio,
                            "output_audio": rvc_output,
                            "config": "modules/voice_conversion_rvc/config/settings.yaml",
                        },
                    ))

                if run_lipsync:
                    if "MuseTalk" in lipsync_method:
                        step_payloads.append((
                            "MuseTalk 립싱크",
                            "lipsync-musetalk/",
                            {
                                "input_video": lipsync_input_video,
                                "input_audio": lipsync_input_audio,
                                "output_video": lipsync_output,
                                "config": "modules/lipsync_musetalk/config/settings.yaml", # Default config for MuseTalk
                            },
                        ))
                    else:
                        step_payloads.append((
                            "Wav2Lip 립싱크",
                            "lipsync/",
                            {
                                "input_video": lipsync_input_video,
                                "input_audio": lipsync_input_audio,
                                "output_video": lipsync_output,
                                "config": str(DEFAULT_LIPSYNC_CONFIG_PATH),
                            },
                        ))

                success = True
                for label, endpoint, payload in step_payloads:
                    # Wav2Lip 립싱크 단계는 시간이 오래 걸리므로 비동기 모드로 실행하여
                    # jobs 상태를 폴링하면서 진행 상황을 표시한다.
                    async_mode = endpoint == "lipsync/"
                    with st.spinner(f"{label} 실행 중..."):
                        result = execute_step(endpoint, payload, async_mode=async_mode)
                    
                    if result is None:
                        st.error(f"{label} 단계에서 오류가 발생했습니다. 로그를 확인해 주세요.")
                        success = False
                        break
                    
                    # 결과 시각화
                    st.divider()
                    st.markdown(f"**✅ {label} 완료 - 결과 확인**")
                    
                    if endpoint == "audio/extract":
                        if os.path.exists(payload["output_audio"]):
                            st.audio(payload["output_audio"])
                    
                    elif endpoint in ["stt/", "stt-gemini/", "text/process"]:
                        if os.path.exists(payload["output_json"]):
                            try:
                                with open(payload["output_json"], "r", encoding="utf-8") as f:
                                    data = json.load(f)
                                
                                # 데이터프레임으로 깔끔하게 표시
                                if isinstance(data, list):
                                    import pandas as pd
                                    
                                    # 표시할 데이터 구성
                                    table_data = []
                                    for item in data:
                                        row = {
                                            "Start": item.get("start") or item.get("startTime"),
                                            "End": item.get("end") or item.get("endTime"),
                                            "Original Text": item.get("text") or item.get("originalText"),
                                        }
                                        # 번역된 텍스트가 있으면 추가
                                        if item.get("translated") or item.get("translatedText"):
                                            row["Translated Text"] = item.get("translated") or item.get("translatedText")
                                        
                                        table_data.append(row)
                                    
                                    if table_data:
                                        df = pd.DataFrame(table_data)
                                        st.dataframe(df, use_container_width=True)
                                    else:
                                        st.info("표시할 텍스트 데이터가 없습니다.")
                                
                                # 원본 JSON도 접어서 볼 수 있게 유지
                                with st.expander("원본 JSON 데이터 보기"):
                                    st.json(data)
                            except Exception as e:
                                st.warning(f"결과 파일을 읽을 수 없습니다: {e}")

                    elif endpoint in ["tts/", "tts-backup/", "tts-gemini/", "rvc/"]:
                        if os.path.exists(payload["output_audio"]):
                            st.audio(payload["output_audio"])
                    
                    elif endpoint == "lipsync/":
                        if os.path.exists(payload["output_video"]):
                            st.video(payload["output_video"])
                if success:
                    st.success("선택한 파이프라인 단계 실행이 완료되었습니다.")
