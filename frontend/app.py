from __future__ import annotations
import json
from pathlib import Path
import os
from typing import Any
import time

import requests
import streamlit as st
import yaml


st.set_page_config(page_title="Padiem RnD Dubbing Pipeline", layout="wide")


def build_theme_assets(mode: str) -> tuple[str, str]:
    if mode == "라이트 모드":
        palette = {
            "body": "#f7f8fa",
            "text": "#111318",
            "card_bg": "#ffffff",
            "card_border": "rgba(15,17,26,0.08)",
            "gradient": "linear-gradient(180deg, #ffffff 0%, #f3f4f8 70%, #e6e8f0 100%)",
            "button_text": "#11131a",
            "hero_bg": "linear-gradient(120deg, rgba(255,255,255,0.98), rgba(227,233,255,0.92))",
            "hero_text": "#111318",
            "caption": "#5a5f6e",
            "divider": "rgba(17,19,26,0.12)",
            "input_bg": "#ffffff",
            "input_text": "#111318",
            "input_border": "rgba(15,17,26,0.15)",
            "accent": "#f97316",
        }
    else:
        palette = {
            "body": "#0f1116",
            "text": "#f5f5f7",
            "card_bg": "rgba(255,255,255,0.04)",
            "card_border": "rgba(255,255,255,0.08)",
            "gradient": "linear-gradient(135deg, #11131a 0%, #1c1f2a 100%)",
            "button_text": "#11131a",
            "hero_bg": "linear-gradient(120deg, rgba(255,255,255,0.12), rgba(17,19,26,0.6))",
            "hero_text": "#f5f5f7",
            "caption": "#d1d1d6",
            "divider": "rgba(255,255,255,0.15)",
            "input_bg": "rgba(255,255,255,0.08)",
            "input_text": "#f5f5f7",
            "input_border": "rgba(255,255,255,0.2)",
            "accent": "#ff9f45",
        }

    css = f"""
    <style>
    body {{background: {palette['body']}; color: {palette['text']}; font-family: 'Inter', sans-serif;}}
    .main {{background: {palette['gradient']}; padding: 2rem 3rem;}}
    h1, h2, h3 {{color: {palette['text']} !important;}}
    .section-card {{background: {palette['card_bg']}; border: 1px solid {palette['card_border']}; border-radius: 20px; padding: 1.5rem 1.75rem; box-shadow: 0 25px 55px rgba(15,17,26,0.08); margin-bottom: 1.5rem;}}
    .stButton>button {{background: linear-gradient(120deg, {palette['accent']}, #ffcf73); color: {palette['button_text']}; border: none; border-radius: 999px; padding: 0.65rem 1.75rem; font-weight: 600;}}
    .stButton>button:hover {{box-shadow: 0 15px 30px rgba(249,115,22,0.25);}}
    .stFileUploader>label div[data-testid="stFileUploaderDropzone"] {{border-radius: 16px; border: 1px dashed {palette['input_border']}; background: {palette['input_bg']}; color: {palette['input_text']}; box-shadow: inset 0 0 0 1px rgba(255,255,255,0.02);}}
    .stFileUploader>label p {{color: {palette['input_text']} !important;}}
    .stTextInput>div>div>input {{background: {palette['input_bg']}; color: {palette['input_text']}; border-radius: 12px; border: 1px solid {palette['input_border']}; box-shadow: none;}}
    .stTextInput>label, .stSelectbox>label, .stFileUploader>label, .stSlider>label {{color: {palette['text']} !important; font-weight: 600;}}
    .stSelectbox>div>div {{color: {palette['text']};}}
    .stExpander {{background: {palette['card_bg']} !important; border-radius: 18px; border: 1px solid {palette['card_border']} !important;}}
    .stExpander>div:first-child {{background: transparent !important; color: {palette['text']} !important;}}
    .stCheckbox>label {{color: {palette['text']} !important;}}
    div[data-testid="column"]:nth-child(2) > div:first-child {{border-left: 1px solid {palette['divider']}; padding-left: 1.25rem; margin-left: 1rem;}}
    div[data-testid="column"]:nth-child(1) > div:first-child {{padding-right: 0.75rem;}}
    .hero {{padding: 1.5rem 2rem; border-radius: 24px; background: {palette['hero_bg']}; border: 1px solid {palette['card_border']}; box-shadow: 0 35px 60px rgba(0,0,0,0.25); margin-bottom: 1.5rem;}}
    .hero h1 {{margin-bottom: 0.5rem; font-size: 2rem; color: {palette['hero_text']};}}
    .hero p {{color: {palette['caption']}; margin: 0;}}
    </style>
    """

    hero = f"""
    <div class=\"hero\">
        <h1>Padiem Modular Dubbing</h1>
        <p>{mode} · ChatGPT/ElevenLabs 감성의 깔끔한 인터페이스로 전체 파이프라인을 제어하세요.</p>
    </div>
    """
    return css, hero


theme_mode = st.sidebar.selectbox("테마", ["라이트 모드", "다크 모드"], index=0)
css_block, hero_block = build_theme_assets(theme_mode)
st.markdown(css_block, unsafe_allow_html=True)
st.markdown(hero_block, unsafe_allow_html=True)

api_base = st.sidebar.text_input("API 기본 URL", value="http://localhost:8000")
poll_interval = st.sidebar.number_input(
    "작업 폴링 간격(초)", min_value=0.5, max_value=10.0, value=1.0, step=0.5
)
max_polls = st.sidebar.number_input(
    "최대 폴링 횟수", min_value=1, max_value=50, value=10, step=1
)

LANGUAGE_OPTIONS = [
    ("auto", "자동 감지 (Auto)"),
    ("ko", "한국어"),
    ("en", "영어"),
    ("fr", "프랑스어"),
    ("es", "스페인어"),
    ("zh", "중국어"),
    ("ja", "일본어"),
    ("de", "독일어"),
    ("ru", "러시아어"),
]
LANGUAGE_LABEL = {code: label for code, label in LANGUAGE_OPTIONS}
TARGET_LANG_CODES = [code for code, _ in LANGUAGE_OPTIONS if code != "auto"]
DEFAULT_STT_CONFIG_PATH = Path("modules/stt_whisper/config/settings.yaml")
DEFAULT_TEXT_CONFIG_PATH = Path("modules/text_processor/config/settings.yaml")
STT_UI_OVERRIDE_PATH = DEFAULT_STT_CONFIG_PATH.with_name("ui_override.yaml")
TEXT_UI_OVERRIDE_PATH = DEFAULT_TEXT_CONFIG_PATH.with_name("ui_override.yaml")


def load_yaml_file(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {}
    try:
        return yaml.safe_load(path.read_text(encoding="utf-8")) or {}
    except yaml.YAMLError as exc:
        st.warning(f"설정 파일을 읽을 수 없습니다: {path} ({exc})")
        return {}


def write_yaml_file(path: Path, data: dict[str, Any]) -> str:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(yaml.safe_dump(data, allow_unicode=True, sort_keys=False), encoding="utf-8")
    return str(path)


def cleanup_temp_file(path: Path) -> None:
    if path.exists():
        try:
            path.unlink()
        except OSError as exc:
            st.warning(f"임시 설정 파일을 삭제하지 못했습니다: {path} ({exc})")


def build_override_config(
    user_path: str | None,
    default_path: Path,
    override_path: Path,
    overrides: dict[str, Any],
) -> str:
    base_config: dict[str, Any] = {}
    for candidate in [user_path, str(default_path)]:
        if not candidate:
            continue
        candidate_path = Path(candidate)
        if candidate_path.exists():
            base_config = load_yaml_file(candidate_path)
            break
    base_config.update({k: v for k, v in overrides.items() if v is not None})
    return write_yaml_file(override_path, base_config)


def display_text_summary(json_path: str) -> None:
    path = Path(json_path)
    if not path.exists():
        st.info(f"결과 파일을 찾을 수 없습니다: {path}")
        return
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        st.error(f"JSON을 파싱할 수 없습니다: {exc}")
        return
    segments = data.get("segments", [])
    st.caption(f"세그먼트 {len(segments)}개")
    needs_review = [seg for seg in segments if seg.get("needs_review")]
    st.write(f"검토 필요 세그먼트: {len(needs_review)}")
    if needs_review:
        preview_cols = [
            {
                "id": seg.get("id"),
                "start": seg.get("start"),
                "end": seg.get("end"),
                "ratio": seg.get("syllable_ratio"),
                "notes": seg.get("notes"),
            }
            for seg in needs_review
        ]
        st.dataframe(preview_cols, use_container_width=True)


def text_input_with_state(label: str, key: str, default: str) -> str:
    if key not in st.session_state:
        st.session_state[key] = default
    return st.text_input(label, key=key)


def sanitize_run_name(name: str) -> str:
    sanitized = name.strip().replace("/", "_").replace("\\", "_")
    return sanitized or "run"


def update_run_defaults(input_media_path: str) -> None:
    if not input_media_path:
        return
    run_name_raw = Path(input_media_path).stem
    if not run_name_raw:
        return

    run_name = sanitize_run_name(run_name_raw)
    previous = st.session_state.get("current_run_name")
    if previous == run_name:
        return

    run_dir = Path("data/runs") / run_name
    st.session_state["current_run_name"] = run_name
    st.session_state["run_base_dir"] = str(run_dir)

    defaults = {
        "audio_output_path": run_dir / f"{run_name}_audio.wav",
        "stt_input_audio_path": run_dir / f"{run_name}_audio.wav",
        "stt_output_path": run_dir / f"{run_name}_result.json",
        "text_process_input_path": run_dir / f"{run_name}_result.json",
        "text_process_output_path": run_dir / f"{run_name}_text.json",
        "tts_input_json_path": run_dir / f"{run_name}_text.json",
        "tts_output_path": run_dir / f"{run_name}_valle.wav",
        "xtts_input_json_path": run_dir / f"{run_name}_text.json",
        "xtts_output_path": run_dir / f"{run_name}_xtts.wav",
        "rvc_input_audio_path": run_dir / f"{run_name}_valle.wav",
        "rvc_output_path": run_dir / f"{run_name}_rvc.wav",
        "lipsync_input_audio_path": run_dir / f"{run_name}_rvc.wav",
        "lipsync_output_path": run_dir / f"{run_name}_wav2lip.mp4",
    }

    defaults["lipsync_input_video_path"] = input_media_path

    for key, path in defaults.items():
        st.session_state[key] = str(path)


def handle_file_input(
    label: str,
    key_prefix: str,
    default_path: str,
    upload_label: str,
    allowed_types: list[str] | None = None,
) -> str:
    path_key = f"{key_prefix}_path"
    if path_key not in st.session_state:
        st.session_state[path_key] = default_path

    uploaded = st.file_uploader(upload_label, type=allowed_types, key=f"{key_prefix}_upload")
    if uploaded is not None:
        upload_dir = Path("data/uploads")
        upload_dir.mkdir(parents=True, exist_ok=True)
        target_path = upload_dir / uploaded.name
        target_path.write_bytes(uploaded.getbuffer())
        st.session_state[path_key] = str(target_path)
        st.success(f"업로드 완료: {target_path}")
    path_value = st.text_input(label, key=path_key)
    return path_value


def call_api(endpoint: str, payload: dict[str, Any]) -> dict[str, Any]:
    """API 호출 공통 함수."""
    url = f"{api_base.rstrip('/')}/{endpoint.lstrip('/')}"
    try:
        response = requests.post(url, json=payload, timeout=60)
        response.raise_for_status()
        return response.json()
    except requests.RequestException as exc:
        st.error(f"API 호출 실패: {exc}")
        raise


def get_job_status(job_id: str) -> dict[str, Any]:
    """작업 상태 조회."""
    url = f"{api_base.rstrip('/')}/jobs/{job_id}"
    try:
        response = requests.get(url, timeout=10)
        response.raise_for_status()
        return response.json()
    except requests.RequestException as exc:
        st.error(f"작업 상태 조회 실패: {exc}")
        raise


def execute_step(endpoint: str, payload: dict[str, Any], async_mode: bool) -> dict[str, Any] | None:
    """단계 실행 및 결과 표시."""
    request_payload = dict(payload)
    if async_mode:
        request_payload["async_run"] = True

    try:
        response = call_api(endpoint, request_payload)
    except Exception:
        return None

    if async_mode and "job_id" in response:
        job_id = response["job_id"]
        st.info(f"작업이 큐에 등록되었습니다. Job ID: {job_id}")
        job_result: dict[str, Any] | None = None
        with st.spinner("작업 진행 상태 확인 중..."):
            for _ in range(int(max_polls)):
                try:
                    job_result = get_job_status(job_id)
                except Exception:
                    return
                status = job_result.get("status")
                if status in {"success", "failed"}:
                    break
                time.sleep(float(poll_interval))
        if not job_result:
            st.warning("작업 상태를 확인할 수 없습니다.")
            return None
        status = job_result.get("status")
        if status == "success":
            st.success(json.dumps(job_result.get("result", {}), ensure_ascii=False, indent=2))
        elif status == "failed":
            st.error(job_result.get("error", "작업이 실패했습니다."))
        else:
            st.warning("작업이 아직 진행 중입니다. Jobs 탭에서 수동 확인이 필요합니다.")
        return job_result

    st.success(json.dumps(response, ensure_ascii=False, indent=2))
    return response


with st.expander("오디오 추출", expanded=True):
    st.write("동영상/미디어에서 오디오를 추출합니다.")
    col_input, col_config = st.columns([2, 1])

    with col_input:
        st.markdown("**입력 미디어 (영상/음성 파일)**")
        input_media = handle_file_input(
            "입력 미디어 경로",
            "audio_input_media",
            "data/inputs/source.mp4",
            "입력 미디어 업로드",
            ["mp4", "mov", "mkv", "avi", "mp3", "wav", "m4a", "aac", "flac", "ogg"],
        )
        update_run_defaults(input_media)
        if run_dir := st.session_state.get("run_base_dir"):
            st.caption(f"현재 실행 폴더: {run_dir}")
        output_audio = text_input_with_state(
            "출력 오디오 경로",
            "audio_output_path",
            "data/intermediates/source_audio.wav",
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
        execute_step("audio/extract", payload, audio_async)

with st.expander("Whisper STT"):
    st.write("오디오를 텍스트로 변환합니다.")
    col_input, col_config = st.columns([2, 1])

    with col_input:
        st.markdown("**입력/출력 파일**")
        input_audio = handle_file_input(
            "STT 입력 오디오 경로",
            "stt_input_audio",
            "data/intermediates/source_audio.wav",
            "STT 입력 오디오 업로드",
            ["wav", "mp3", "flac", "m4a"],
        )
        stt_output = text_input_with_state(
            "STT 결과 JSON 경로",
            "stt_output_path",
            "data/intermediates/stt_result.json",
        )

    with col_config:
        st.markdown("**설정**")
        st.caption("기본적으로 auto 감지를 사용하며, 필요 시 언어와 설정 파일을 지정하세요.")
        stt_config = handle_file_input(
            "STT 설정 파일 경로",
            "stt_config",
            str(DEFAULT_STT_CONFIG_PATH),
            "STT 설정 업로드(선택)",
            ["yaml", "yml"],
        )
        stt_language = st.selectbox(
            "STT 언어",
            options=[code for code, _ in LANGUAGE_OPTIONS],
            format_func=lambda code: LANGUAGE_LABEL.get(code, code),
            index=0,
            key="stt_language_select",
        )

    stt_async = st.checkbox("비동기 실행", key="stt_async")
    if st.button("STT 실행"):
        effective_config = stt_config or str(DEFAULT_STT_CONFIG_PATH)
        override_used = False
        if stt_language != "auto":
            effective_config = build_override_config(
                stt_config,
                DEFAULT_STT_CONFIG_PATH,
                STT_UI_OVERRIDE_PATH,
                {"language": stt_language, "word_timestamps": True},
            )
            override_used = True
        payload = {
            "input_audio": input_audio,
            "output_json": stt_output,
            "config": effective_config,
        }
        execute_step("stt/", payload, stt_async)
        if override_used:
            cleanup_temp_file(STT_UI_OVERRIDE_PATH)

with st.expander("텍스트 처리/번역"):
    st.write("STT 결과를 전처리하거나 번역합니다.")
    col_input, col_config = st.columns([2, 1])

    with col_input:
        st.markdown("**입력/출력 JSON**")
        text_input = handle_file_input(
            "텍스트 처리 입력 JSON 경로",
            "text_process_input",
            "data/intermediates/stt_result.json",
            "텍스트 입력 JSON 업로드",
            ["json"],
        )
        text_output = text_input_with_state(
            "텍스트 처리 결과 JSON 경로",
            "text_process_output_path",
            "data/intermediates/text_processed.json",
        )

    with col_config:
        st.markdown("**설정**")
        text_config = handle_file_input(
            "텍스트 처리 설정 파일 경로",
            "text_process_config",
            str(DEFAULT_TEXT_CONFIG_PATH),
            "텍스트 설정 업로드(선택)",
            ["yaml", "yml", "json"],
        )
        source_lang = st.selectbox(
            "원본 언어",
            options=[code for code, _ in LANGUAGE_OPTIONS if code != "auto"],
            format_func=lambda code: LANGUAGE_LABEL.get(code, code),
            index=0,
            key="text_source_lang",
        )
        target_lang = st.selectbox(
            "번역 언어",
            options=TARGET_LANG_CODES,
            format_func=lambda code: LANGUAGE_LABEL.get(code, code),
            index=TARGET_LANG_CODES.index("en"),
            key="text_target_lang",
        )
        syllable_tol = st.slider(
            "허용 음절 비율 (±)", min_value=0.05, max_value=0.3, value=0.1, step=0.01, key="text_syllable_tol"
        )
        enforce_timing = st.checkbox("타이밍 엄격 모드", value=True, key="text_enforce_timing")
    text_async = st.checkbox("비동기 실행", key="text_async")
    if st.button("텍스트 처리 실행"):
        effective_config = build_override_config(
            text_config,
            DEFAULT_TEXT_CONFIG_PATH,
            TEXT_UI_OVERRIDE_PATH,
            {
                "source_language": source_lang,
                "target_language": target_lang,
                "syllable_tolerance": float(syllable_tol),
                "enforce_timing": enforce_timing,
            },
        )
        payload = {
            "input_json": text_input,
            "output_json": text_output,
            "config": effective_config,
        }
        result = execute_step("text/process", payload, text_async)
        cleanup_temp_file(TEXT_UI_OVERRIDE_PATH)
        if result is not None:
            st.divider()
            st.subheader("텍스트 처리 요약")
            display_text_summary(text_output)

with st.expander("VALL-E X 합성"):
    st.write("전처리된 텍스트를 기반으로 음성을 합성합니다.")
    col_input, col_config = st.columns([2, 1])

    with col_input:
        tts_input = handle_file_input(
            "TTS 입력 JSON 경로",
            "tts_input_json",
            "data/intermediates/text_processed.json",
            "TTS 입력 JSON 업로드",
            ["json"],
        )
        tts_output = text_input_with_state(
            "TTS 출력 WAV 경로",
            "tts_output_path",
            "data/intermediates/tts_output.wav",
        )

    with col_config:
        tts_config = handle_file_input(
            "TTS 설정 파일 경로",
            "tts_config",
            "",
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
        execute_step("tts/", payload, tts_async)

with st.expander("XTTS 백업 합성"):
    st.write("백업 TTS 경로를 통해 음성을 합성합니다.")
    col_input, col_config = st.columns([2, 1])

    with col_input:
        xtts_input = handle_file_input(
            "XTTS 입력 JSON 경로",
            "xtts_input_json",
            "data/intermediates/text_processed.json",
            "XTTS 입력 JSON 업로드",
            ["json"],
        )
        xtts_output = text_input_with_state(
            "XTTS 출력 WAV 경로",
            "xtts_output_path",
            "data/intermediates/tts_backup_output.wav",
        )

    with col_config:
        xtts_config = handle_file_input(
            "XTTS 설정 파일 경로",
            "xtts_config",
            "",
            "XTTS 설정 업로드(선택)",
            ["yaml", "yml", "json"],
        )
    xtts_async = st.checkbox("비동기 실행", key="xtts_async")
    if st.button("XTTS 합성 실행"):
        payload = {
            "input_json": xtts_input,
            "output_audio": xtts_output,
            "config": xtts_config or None,
        }
        execute_step("tts-backup/", payload, xtts_async)

with st.expander("RVC 음성 변환"):
    st.write("합성된 음성을 타깃 화자의 음색으로 변환합니다.")
    col_input, col_config = st.columns([2, 1])

    with col_input:
        rvc_input = handle_file_input(
            "RVC 입력 WAV 경로",
            "rvc_input_audio",
            "data/intermediates/tts_output.wav",
            "RVC 입력 오디오 업로드",
            ["wav", "mp3", "flac", "m4a"],
        )
        rvc_output = text_input_with_state(
            "RVC 출력 WAV 경로",
            "rvc_output_path",
            "data/intermediates/rvc_output.wav",
        )

    with col_config:
        rvc_config = handle_file_input(
            "RVC 설정 파일 경로",
            "rvc_config",
            "",
            "RVC 설정 업로드(선택)",
            ["yaml", "yml", "json"],
        )
    rvc_async = st.checkbox("비동기 실행", key="rvc_async")
    if st.button("RVC 변환 실행"):
        payload = {
            "input_audio": rvc_input,
            "output_audio": rvc_output,
            "config": rvc_config or None,
        }
        execute_step("rvc/", payload, rvc_async)

with st.expander("Wav2Lip 립싱크"):
    st.write("변환된 음성을 영상에 립싱크로 합성합니다.")
    col_input, col_config = st.columns([2, 1])

    with col_input:
        lipsync_video = handle_file_input(
            "립싱크 입력 영상 경로",
            "lipsync_input_video",
            "data/inputs/source.mp4",
            "립싱크 영상 업로드",
            ["mp4", "mov", "mkv", "avi"],
        )
        lipsync_audio = handle_file_input(
            "립싱크 입력 오디오 경로",
            "lipsync_input_audio",
            "data/intermediates/rvc_output.wav",
            "립싱크 오디오 업로드",
            ["wav", "mp3", "flac", "m4a"],
        )
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
        execute_step("lipsync/", payload, lipsync_async)

with st.expander("전체 파이프라인 실행", expanded=False):
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

st.sidebar.markdown("---")
st.sidebar.write("비동기 실행을 사용할 경우 Jobs 엔드포인트에서 상태를 추가로 확인할 수 있습니다.")
