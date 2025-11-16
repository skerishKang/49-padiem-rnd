from __future__ import annotations
import json
from pathlib import Path
from typing import Any
import time

import requests
import streamlit as st


st.set_page_config(page_title="Padiem RnD Dubbing Pipeline", layout="wide")

st.title("Padiem RnD 모듈형 더빙 파이프라인 프로토타입 UI")
st.write("백엔드 API를 호출해 모듈 동작 흐름을 검증하는 초기 프로토타입입니다.")

api_base = st.sidebar.text_input("API 기본 URL", value="http://localhost:8000")
poll_interval = st.sidebar.number_input(
    "작업 폴링 간격(초)", min_value=0.5, max_value=10.0, value=1.0, step=0.5
)
max_polls = st.sidebar.number_input(
    "최대 폴링 횟수", min_value=1, max_value=50, value=10, step=1
)


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


def execute_step(endpoint: str, payload: dict[str, Any], async_mode: bool) -> None:
    """단계 실행 및 결과 표시."""
    request_payload = dict(payload)
    if async_mode:
        request_payload["async_run"] = True

    try:
        response = call_api(endpoint, request_payload)
    except Exception:
        return

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
            return
        status = job_result.get("status")
        if status == "success":
            st.success(json.dumps(job_result.get("result", {}), ensure_ascii=False, indent=2))
        elif status == "failed":
            st.error(job_result.get("error", "작업이 실패했습니다."))
        else:
            st.warning("작업이 아직 진행 중입니다. Jobs 탭에서 수동 확인이 필요합니다.")
        return

    st.success(json.dumps(response, ensure_ascii=False, indent=2))


with st.expander("오디오 추출", expanded=True):
    st.write("동영상/미디어에서 오디오를 추출합니다.")
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
    stt_config = handle_file_input(
        "STT 설정 파일 경로",
        "stt_config",
        "modules/stt_whisper/config/settings.yaml",
        "STT 설정 업로드(선택)",
        ["yaml", "yml"],
    )
    stt_async = st.checkbox("비동기 실행", key="stt_async")
    if st.button("STT 실행"):
        payload = {
            "input_audio": input_audio,
            "output_json": stt_output,
            "config": stt_config or None,
        }
        execute_step("stt/", payload, stt_async)

with st.expander("텍스트 처리/번역"):
    st.write("STT 결과를 전처리하거나 번역합니다.")
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
    text_config = handle_file_input(
        "텍스트 처리 설정 파일 경로",
        "text_process_config",
        "",
        "텍스트 설정 업로드(선택)",
        ["yaml", "yml", "json"],
    )
    text_async = st.checkbox("비동기 실행", key="text_async")
    if st.button("텍스트 처리 실행"):
        payload = {
            "input_json": text_input,
            "output_json": text_output,
            "config": text_config or None,
        }
        execute_step("text/process", payload, text_async)

with st.expander("VALL-E X 합성"):
    st.write("전처리된 텍스트를 기반으로 음성을 합성합니다.")
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

st.sidebar.markdown("---")
st.sidebar.write("비동기 실행을 사용할 경우 Jobs 엔드포인트에서 상태를 추가로 확인할 수 있습니다.")
