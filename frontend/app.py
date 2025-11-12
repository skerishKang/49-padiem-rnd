from __future__ import annotations
import json
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
    input_media = st.text_input("입력 미디어 경로", value="data/inputs/source.mp4")
    output_audio = st.text_input("출력 오디오 경로", value="data/intermediates/source_audio.wav")
    config_path = st.text_input("설정 파일 경로", value="")
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
    input_audio = st.text_input("STT 입력 오디오 경로", value="data/intermediates/source_audio.wav")
    stt_output = st.text_input("STT 결과 JSON 경로", value="data/intermediates/stt_result.json")
    stt_config = st.text_input("STT 설정 파일 경로", value="modules/stt_whisper/config/settings.yaml")
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
    text_input = st.text_input("텍스트 처리 입력 JSON 경로", value="data/intermediates/stt_result.json")
    text_output = st.text_input("텍스트 처리 결과 JSON 경로", value="data/intermediates/text_processed.json")
    text_config = st.text_input("텍스트 처리 설정 파일 경로", value="")
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
    tts_input = st.text_input("TTS 입력 JSON 경로", value="data/intermediates/text_processed.json")
    tts_output = st.text_input("TTS 출력 WAV 경로", value="data/intermediates/tts_output.wav")
    tts_config = st.text_input("TTS 설정 파일 경로", value="")
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
    xtts_input = st.text_input("XTTS 입력 JSON 경로", value="data/intermediates/text_processed.json")
    xtts_output = st.text_input("XTTS 출력 WAV 경로", value="data/intermediates/tts_backup_output.wav")
    xtts_config = st.text_input("XTTS 설정 파일 경로", value="")
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
    rvc_input = st.text_input("RVC 입력 WAV 경로", value="data/intermediates/tts_output.wav")
    rvc_output = st.text_input("RVC 출력 WAV 경로", value="data/intermediates/rvc_output.wav")
    rvc_config = st.text_input("RVC 설정 파일 경로", value="")
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
    lipsync_video = st.text_input("립싱크 입력 영상 경로", value="data/inputs/source.mp4")
    lipsync_audio = st.text_input("립싱크 입력 오디오 경로", value="data/intermediates/rvc_output.wav")
    lipsync_output = st.text_input("립싱크 출력 영상 경로", value="data/outputs/final_dubbed.mp4")
    lipsync_config = st.text_input("립싱크 설정 파일 경로", value="")
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
