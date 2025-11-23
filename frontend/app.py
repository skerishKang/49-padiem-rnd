from __future__ import annotations
import json
from pathlib import Path
import os
from typing import Any
import time

import requests
import streamlit as st
import yaml
import pandas as pd

from session_utils import load_session_data, save_session_data


# MUST be the first Streamlit command
st.set_page_config(page_title="Padiem RnD Dubbing Pipeline", layout="wide")


# 저장된 세션 데이터 불러오기 (Streamlit 명령 아님)
saved_session = load_session_data()

# 주요 경로들을 세션에 복원
if saved_session:
    for key, value in saved_session.items():
        if key not in st.session_state:
            st.session_state[key] = value
    # STT 결과 -> 텍스트 처리 입력, 텍스트 결과 -> TTS 입력 연결을 복원
    def _restore_downstream_links() -> None:
        changed = False

        last_stt = st.session_state.get("last_stt_output")
        if last_stt:
            text_input = st.session_state.get("text_process_input_path")
            if not text_input or text_input in {
                "data/intermediates/source_audio_result.json",
                "data/intermediates/stt_result.json",
            }:
                st.session_state["text_process_input_path"] = last_stt
                text_input = last_stt
                changed = True

            text_output = st.session_state.get("text_process_output_path")
            if not text_output or text_output in {
                "data/intermediates/text_process_result.json",
                "data/intermediates/source_audio_result_text.json",
            }:
                candidate = Path(text_input)
                st.session_state["text_process_output_path"] = str(
                    candidate.with_name(f"{candidate.stem}_text.json")
                )
                changed = True

        last_text = st.session_state.get("last_text_output")
        if last_text:
            for key in ("tts_input_json_path", "xtts_input_json_path"):
                current = st.session_state.get(key)
                if not current or current in {
                    "data/intermediates/text_process_result.json",
                    "data/intermediates/source_audio_result_text.json",
                }:
                    st.session_state[key] = last_text
                    changed = True

        if changed:
            save_session_data(
                {
                    "text_process_input_path": st.session_state.get("text_process_input_path"),
                    "text_process_output_path": st.session_state.get("text_process_output_path"),
                    "tts_input_json_path": st.session_state.get("tts_input_json_path"),
                    "xtts_input_json_path": st.session_state.get("xtts_input_json_path"),
                }
            )

    _restore_downstream_links()

    def _restore_valle_output() -> None:
        """VALL-E X 출력이 있으면 세션에 복원."""
        if "last_tts_output" not in st.session_state:
            # 1. 세션 데이터에서 확인
            if last_out := saved_session.get("last_tts_output"):
                 if Path(last_out).exists():
                     st.session_state["last_tts_output"] = last_out
                     return

            # 2. 파일 시스템에서 추론
            if text_out := st.session_state.get("text_process_output_path"):
                 expected_out = Path(text_out).parent / f"{Path(text_out).stem}_valle.wav"
                 if expected_out.exists():
                     st.session_state["last_tts_output"] = str(expected_out)

    _restore_valle_output()

    def _restore_xtts_output() -> None:
        """XTTS 출력이 있으면 세션에 복원."""
        if "last_xtts_output" not in st.session_state:
            # 1. 세션 데이터에서 확인
            if last_out := saved_session.get("last_xtts_output"):
                 if Path(last_out).exists():
                     st.session_state["last_xtts_output"] = last_out
                     return

            # 2. 파일 시스템에서 추론
            if xtts_out := st.session_state.get("xtts_output_path"):
                 if Path(xtts_out).exists():
                     st.session_state["last_xtts_output"] = xtts_out

    _restore_xtts_output()


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


theme_mode = st.sidebar.selectbox("테마", ["라이트 모드", "다크 모드"], index=1)
css_block, hero_block = build_theme_assets(theme_mode)
st.markdown(css_block, unsafe_allow_html=True)
st.markdown(hero_block, unsafe_allow_html=True)

api_base = st.sidebar.text_input("API 기본 URL", value="http://localhost:8010")
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
    
    # 전체 번역 텍스트 구성 (processed_text 필드 병합)
    full_text = ""
    if segments:
        full_text = " ".join([seg.get("processed_text", seg.get("text", "")) for seg in segments])

    st.markdown("### 📝 텍스트 처리 결과")
    
    if segments:
        # 스크롤 가능한 컨테이너 (높이 300px)
        with st.container(height=300):
            for segment in segments:
                start = format_timestamp(segment.get("start", 0))
                end = format_timestamp(segment.get("end", 0))
                # 번역된 텍스트가 있으면 사용, 없으면 원본
                text = segment.get("processed_text", segment.get("text", ""))
                st.markdown(f"**[{start} - {end}]** {text}")
    else:
        st.info(full_text or "텍스트 없음")

    # 검토 필요 항목
    needs_review = [seg for seg in segments if seg.get("needs_review")]
    if needs_review:
        st.warning(f"⚠️ 검토가 필요한 세그먼트가 {len(needs_review)}개 있습니다.")
        st.dataframe(needs_review)

    # 전체 세그먼트 보기
    if st.checkbox("전체 세그먼트 상세 정보 보기", key="text_process_detail"):
        st.dataframe(segments)


def format_timestamp(seconds: float) -> str:
    mm = int(seconds // 60)
    ss = int(seconds % 60)
    return f"{mm:02d}:{ss:02d}"


def display_stt_result(json_path: str) -> None:
    path = Path(json_path)
    if not path.exists():
        return
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return

    st.markdown("### 📝 전사 결과 (수정 가능)")
    st.caption("아래 표에서 텍스트를 직접 수정할 수 있습니다. 수정 후 **[수정 사항 저장]** 버튼을 꼭 눌러주세요.")
    
    if "segments" in data:
        df = pd.DataFrame(data["segments"])
        # 컬럼 순서 및 표시 설정
        column_config = {
            "start": st.column_config.NumberColumn("시작(초)", format="%.2f", disabled=True),
            "end": st.column_config.NumberColumn("종료(초)", format="%.2f", disabled=True),
            "text": st.column_config.TextColumn("전사 텍스트", width="large"),
        }
        
        # 필요한 컬럼만 선택 (start, end, text가 기본)
        cols = ["start", "end", "text"]
        # 나머지 컬럼도 있다면 포함
        extra_cols = [c for c in df.columns if c not in cols]
        final_cols = cols + extra_cols
        
        edited_df = st.data_editor(
            df[final_cols],
            num_rows="dynamic",
            use_container_width=True,
            key=f"stt_editor_{json_path}",
            column_config=column_config,
            hide_index=True,
        )

        if st.button("수정 사항 저장", key=f"save_stt_{json_path}"):
            try:
                # DataFrame을 딕셔너리 리스트로 변환
                new_segments = edited_df.to_dict(orient="records")
                data["segments"] = new_segments
                
                # 전체 텍스트(text 필드)도 업데이트
                data["text"] = " ".join([str(seg.get("text", "")) for seg in new_segments])
                
                # 파일 저장
                path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
                st.success("✅ 전사 결과가 저장되었습니다. 이제 '텍스트 처리' 단계를 실행하면 수정된 내용이 반영됩니다.")
                
                # 세션 상태 업데이트 (강제 리로드 효과)
                st.session_state["last_stt_output"] = str(path)
                
            except Exception as e:
                st.error(f"저장 중 오류가 발생했습니다: {e}")
            
    else:
        st.info(data.get("text", "텍스트 없음"))


def text_input_with_state(label: str, key: str, default: str) -> str:
    if key not in st.session_state:
        st.session_state[key] = default
    return st.text_input(label, key=key)


def sanitize_run_name(name: str) -> str:
    sanitized = name.strip().replace("/", "_").replace("\\", "_")
    return sanitized or "run"


def update_run_defaults(input_media_path: str, exclude_keys: list[str] | None = None) -> None:
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
        if exclude_keys and key in exclude_keys:
            continue
        try:
            st.session_state[key] = str(path)
        except Exception:
            # 이미 위젯이 생성된 경우 건너뜀
            pass


def update_output_path_from_input(input_path: str, output_key: str, suffix: str) -> None:
    """입력 경로가 변경되면 출력 경로를 자동으로 업데이트"""
    if not input_path or not output_key:
        return
        
    try:
        input_p = Path(input_path)
        # 입력 파일명(확장자 제외) + 접미사
        new_filename = f"{input_p.stem}{suffix}"
        new_output_path = input_p.parent / new_filename
        
        # 현재 세션 값과 다르면 업데이트
        if st.session_state.get(output_key) != str(new_output_path):
            st.session_state[output_key] = str(new_output_path)
    except Exception:
        pass


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


def call_api(endpoint: str, payload: dict[str, Any], timeout: float | None = None) -> dict[str, Any]:
    """API 호출 공통 함수.

    STT(Whisper)처럼 실행 시간이 긴 엔드포인트는 별도 타임아웃을 줄 수 있도록
    timeout 인자를 받도록 확장했습니다.
    """
    url = f"{api_base.rstrip('/')}/{endpoint.lstrip('/')}"
    # 기본 타임아웃은 60초, 별도 지정 시 해당 값 사용
    effective_timeout = timeout or 300.0 # TTS 등 오래 걸리는 작업을 위해 기본값 5분으로 증량
    try:
        response = requests.post(url, json=payload, timeout=effective_timeout)
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

    # STT는 Whisper 모델 로딩/전사 때문에 시간이 오래 걸릴 수 있으므로
    # 동기 실행 시 더 넉넉한 타임아웃을 준다.
    timeout_override: float | None = None
    if not async_mode and endpoint.rstrip("/") == "stt":
        timeout_override = 300.0

    try:
        response = call_api(endpoint, request_payload, timeout=timeout_override)
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
        
        # 초기화: 세션에 last_audio_input_media가 없으면 현재 값으로 설정 (리로드 시 변경 감지 방지)
        if "last_audio_input_media" not in st.session_state:
            st.session_state["last_audio_input_media"] = input_media

        # 변경 감지: 입력이 실제로 바뀌었을 때만 defaults 업데이트
        if input_media != st.session_state.get("last_audio_input_media"):
            update_run_defaults(input_media)
            st.session_state["last_audio_input_media"] = input_media
            
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
        result = execute_step("audio/extract", payload, audio_async)
        if result:
            st.audio(output_audio)
            st.session_state["stt_input_audio_path"] = output_audio
            st.success("다음 단계(STT) 입력이 자동으로 설정되었습니다.")
            
            # 세션 저장 (파일 경로 기억)
            save_session_data({
                "audio_input_media_path": input_media,
                "audio_output_path": output_audio,
                "current_run_name": st.session_state.get("current_run_name"),
                "run_base_dir": st.session_state.get("run_base_dir"),
                "last_audio_input_media": input_media,
            })

with st.expander("Whisper STT", expanded=True):
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

        
        # 변경 감지
        if input_audio != st.session_state.get("last_stt_input_audio"):
            update_run_defaults(input_audio, exclude_keys=["stt_input_audio_path", "audio_output_path"])
            st.session_state["last_stt_input_audio"] = input_audio
            
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
        stt_model = st.selectbox(
            "모델 크기",
            options=["tiny", "base", "small", "medium", "large-v3"],
            index=2, # Default to small
            key="stt_model_select",
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
                {
                    "language": stt_language, 
                    "word_timestamps": True,
                    "model_name": stt_model
                },
            )
            override_used = True
        # 모델만 변경된 경우에도 override 적용
        elif stt_model != "small": # small is default in config
             effective_config = build_override_config(
                stt_config,
                DEFAULT_STT_CONFIG_PATH,
                STT_UI_OVERRIDE_PATH,
                {
                    "model_name": stt_model,
                    "word_timestamps": True
                },
            )
             override_used = True
        payload = {
            "input_audio": input_audio,
            "output_json": stt_output,
            "config": effective_config,
        }
        result = execute_step("stt/", payload, stt_async)
        if result:
            st.session_state["text_process_input_path"] = stt_output
            st.session_state["last_stt_output"] = stt_output  # STT 결과 저장
            st.success("다음 단계(텍스트 처리) 입력이 자동으로 설정되었습니다.")
            
            # 세션 저장
            save_session_data({
                "stt_input_audio_path": input_audio,
                "stt_output_path": stt_output,
                "last_stt_output": stt_output,
                "last_stt_input_audio": input_audio,
                "text_process_input_path": stt_output, # 다음 단계 입력 저장
            })

        if override_used:
            cleanup_temp_file(STT_UI_OVERRIDE_PATH)
    
    # 이전 STT 결과가 있으면 항상 표시
    if "last_stt_output" in st.session_state and st.session_state["last_stt_output"]:
        display_stt_result(st.session_state["last_stt_output"])

with st.expander("텍스트 처리/번역", expanded=True):
    st.write("STT 결과를 전처리하거나 번역합니다.")
    col_input, col_config = st.columns([2, 1])

    with col_input:
        st.markdown("**입력/출력 JSON**")
        input_json = handle_file_input(
            "텍스트 처리 입력 JSON 경로",
            "text_process_input",
            "data/intermediates/source_audio_result.json",
            "텍스트 처리 입력 JSON 업로드",
            ["json"],
        )
        
        # 입력 경로 기반 출력 경로 자동 업데이트
        update_output_path_from_input(input_json, "text_process_output_path", "_text.json")
        
        text_output = text_input_with_state(
            "텍스트 처리 결과 JSON 경로",
            "text_process_output_path",
            "data/intermediates/text_process_result.json",
        )

    with col_config:
        st.markdown("**설정**")
        st.caption("번역할 언어와 Gemini API 키를 설정하세요.")
        
        text_config = handle_file_input(
            "텍스트 처리 설정 파일 경로",
            "text_config",
            str(DEFAULT_TEXT_CONFIG_PATH),
            "텍스트 설정 업로드(선택)",
            ["yaml", "yml"],
        )
        
        source_lang = st.selectbox("원본 언어", ["한국어", "영어", "일본어", "중국어", "자동"], index=4)
        target_lang = st.selectbox("번역 언어", ["영어", "한국어", "일본어", "중국어"], index=0)
        
        gemini_api_key = st.text_input(
            "Gemini API Key", 
            type="password", 
            value=os.getenv("GEMINI_API_KEY", ""),
            help="번역을 위해 필요합니다."
        )

        lang_map = {"한국어": "ko", "영어": "en", "일본어": "ja", "중국어": "zh", "자동": "auto"}
        
        syllable_tolerance = st.slider("허용 음절 비율 (±)", 0.05, 0.30, 0.10, 0.05)
        enforce_timing = st.checkbox("타이밍 엄격 모드", value=True)

    text_async = st.checkbox("비동기 실행", key="text_async")
    if st.button("텍스트 처리 실행"):
        payload = {
            "input_json": input_json,
            "output_json": text_output,
            "config": text_config or None,
            "source_language": lang_map[source_lang],
            "target_language": lang_map[target_lang],
            "syllable_tolerance": syllable_tolerance,
            "enforce_timing": enforce_timing,
            "gemini_api_key": gemini_api_key,
        }
        result = execute_step("text/process", payload, text_async)
        if result:
            st.session_state["tts_input_json_path"] = text_output
            st.session_state["xtts_input_json_path"] = text_output
            st.session_state["last_text_output"] = text_output  # 결과 저장
            st.success("다음 단계(TTS) 입력이 자동으로 설정되었습니다.")

            # 세션 저장
            save_session_data({
                "text_process_input_path": input_json,
                "text_process_output_path": text_output,
                "last_text_output": text_output,
                "tts_input_json_path": text_output, # 다음 단계 입력 저장
                "xtts_input_json_path": text_output, # 다음 단계 입력 저장
            })
    
    # 이전 결과가 있으면 항상 표시
    if "last_text_output" in st.session_state and st.session_state["last_text_output"]:
        st.subheader("텍스트 처리 요약")
        display_text_summary(st.session_state["last_text_output"])

with st.expander("VALL-E X 합성", expanded=True):
    st.write("전처리된 텍스트를 기반으로 음성을 합성합니다.")
    col_input, col_config = st.columns([2, 1])

    with col_input:
        tts_input = handle_file_input(
            "TTS 입력 JSON 경로",
            "tts_input_json",
            "data/intermediates/text_process_result.json",
            "TTS 입력 JSON 업로드",
            ["json"],
        )

        # 입력 경로 기반 출력 경로 자동 업데이트
        update_output_path_from_input(tts_input, "tts_output_path", "_valle.wav")

        tts_output = text_input_with_state(
            "TTS 출력 WAV 경로",
            "tts_output_path",
            "data/intermediates/tts_output.wav",
        )

    with col_config:
        tts_config = handle_file_input(
            "TTS 설정 파일 경로",
            "tts_config",
            "modules/tts_vallex/config/settings.yaml",
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
        result = execute_step("tts/", payload, tts_async)
        if result:
            st.audio(tts_output)
            st.session_state["last_tts_output"] = tts_output
            st.session_state["rvc_input_audio_path"] = tts_output
            st.success("다음 단계(RVC) 입력이 자동으로 설정되었습니다.")

            # 세션 저장
            save_session_data({
                "tts_input_json_path": tts_input,
                "tts_output_path": tts_output,
                "last_tts_output": tts_output,
                "rvc_input_audio_path": tts_output, # 다음 단계 입력 저장
            })
        else:
            # 요청이 실패했더라도 파일이 생성되었다면 재생할 수 있게 안내
            if Path(tts_output).exists():
                st.warning("API 응답은 실패했지만 출력 파일이 생성되었습니다. 아래에서 재생하세요.")
                st.audio(tts_output)
                st.session_state["last_tts_output"] = tts_output
                save_session_data({"last_tts_output": tts_output})

    # 최근 VALL-E X 출력이 있으면 항상 재생 가능하게 노출
    last_tts_out = st.session_state.get("last_tts_output")
    if last_tts_out and Path(last_tts_out).exists():
        st.caption("최근 VALL-E X 출력")
        st.audio(last_tts_out)

with st.expander("XTTS 백업 합성", expanded=True):
    st.write("백업 TTS 경로를 통해 음성을 합성합니다.")
    col_input, col_config = st.columns([2, 1])

    with col_input:
        xtts_input = handle_file_input(
            "XTTS 입력 JSON 경로",
            "xtts_input_json",
            "data/intermediates/text_process_result.json",
            "XTTS 입력 JSON 업로드",
            ["json"],
        )

        # 입력 경로 기반 출력 경로 자동 업데이트
        update_output_path_from_input(xtts_input, "xtts_output_path", "_xtts.wav")

        xtts_output = text_input_with_state(
            "XTTS 출력 WAV 경로",
            "xtts_output_path",
            "data/intermediates/tts_backup_output.wav",
        )

    with col_config:
        xtts_config = handle_file_input(
            "XTTS 설정 파일 경로",
            "xtts_config",
            "modules/tts_xtts/config/settings.yaml",
            "XTTS 설정 업로드(선택)",
            ["yaml", "yml", "json"],
        )
        
        # 기본 스피커 오디오를 원본 입력 오디오로 설정
        default_speaker = st.session_state.get("stt_input_audio_path", "data/inputs/test_audio.wav")
        
        xtts_speaker = handle_file_input(
            "스피커 참조 오디오 (필수)",
            "xtts_speaker_wav",
            default_speaker,
            "스피커 오디오 업로드",
            ["wav", "mp3"],
        )
        
        xtts_lang = st.selectbox(
            "언어 설정 (자동 감지 또는 선택)",
            ["ko", "en", "ja", "zh-cn", "auto"],
            index=4,
            help="텍스트의 언어와 일치시켜주세요. 'auto'는 텍스트 내용을 기반으로 추론합니다."
        )
    xtts_async = st.checkbox("비동기 실행", key="xtts_async")
    if st.button("XTTS 합성 실행"):
        payload = {
            "input_json": xtts_input,
            "output_audio": xtts_output,
            "config": xtts_config or None,
            "speaker_wav": xtts_speaker or None,
            "language": xtts_lang if xtts_lang != "auto" else None,
        }
        result = execute_step("tts-backup/", payload, xtts_async)
        if result:
            # st.audio(xtts_output) # 중복 플레이어 제거 (아래 persistent player 사용)
            st.session_state["rvc_input_audio_path"] = xtts_output
            # st.success("다음 단계(RVC) 입력이 자동으로 설정되었습니다.") # 사용자 요청으로 제거
            
            # 세션 저장
            save_session_data({
                "xtts_input_json_path": xtts_input,
                "xtts_output_path": xtts_output,
                "rvc_input_audio_path": xtts_output, # 다음 단계 입력 저장
                "last_xtts_output": xtts_output, # 최근 출력 저장
            })
            st.session_state["last_xtts_output"] = xtts_output

    # 최근 XTTS 출력이 있으면 항상 재생 가능하게 노출
    last_xtts_out = st.session_state.get("last_xtts_output")
    if last_xtts_out and Path(last_xtts_out).exists():
        st.caption("최근 XTTS 출력")
        st.audio(last_xtts_out)

with st.expander("RVC 음성 변환", expanded=True):
    st.write("합성된 음성을 타깃 화자의 음색으로 변환합니다.")
    col_input, col_config = st.columns([2, 1])

    with col_input:
        rvc_input = handle_file_input(
            "RVC 입력 WAV 경로",
            "rvc_input_audio",
            "data/intermediates/tts_output.wav",
            "RVC 입력 오디오 업로드",
            ["wav", "mp3"],
        )

        # 입력 경로 기반 출력 경로 자동 업데이트
        update_output_path_from_input(rvc_input, "rvc_output_path", "_rvc.wav")

        rvc_output = text_input_with_state(
            "RVC 출력 WAV 경로",
            "rvc_output_path",
            "data/intermediates/rvc_output.wav",
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
        st.caption("RVC 모델 학습이 필요하신가요?")
        if st.button("RVC WebUI 열기 (모델 학습)"):
            # RVC WebUI가 로컬 7865 포트에서 실행 중이라고 가정
            js = "window.open('http://127.0.0.1:7865', '_blank')"
            st.components.v1.html(f"<script>{js}</script>", height=0)
            st.info("브라우저 팝업이 차단되었다면 허용해주세요. (http://127.0.0.1:7865)")
        
        st.info("""
        **설정 파일 작성법**
        1. **RVC WebUI**에서 모델 학습을 완료합니다.
        2. 생성된 `.pth` 파일을 `modules/voice_conversion_rvc/checkpoints/` 폴더에 넣습니다.
        3. `modules/voice_conversion_rvc/config/rvc_template.yaml` 파일을 복사하여 `settings.yaml`을 만듭니다.
        4. `settings.yaml` 안의 `checkpoint` 경로를 내 모델 파일명으로 수정합니다.
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
        
        # 입력 경로 기반 출력 경로 자동 업데이트
        update_output_path_from_input(lipsync_video, "lipsync_output_path", "_wav2lip.mp4")

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
        result = execute_step("lipsync/", payload, lipsync_async)
        if result:
            st.video(lipsync_output)
            
            # 세션 저장
            save_session_data({
                "lipsync_input_video_path": lipsync_video,
                "lipsync_input_audio_path": lipsync_audio,
                "lipsync_output_path": lipsync_output,
            })

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

# === 사이드바: 파일 히스토리 ===
st.sidebar.title("📂 최근 작업 파일")

if "file_history" not in st.session_state:
    st.session_state["file_history"] = []

# 현재 작업 중인 파일 추가
current_file = st.session_state.get("audio_input_media_path")
if current_file:
    history = [f for f in st.session_state["file_history"] if f.get("input") != current_file]
    file_info = {
        "input": current_file,
        "audio_output": st.session_state.get("audio_output_path", ""),
        "stt_output": st.session_state.get("last_stt_output", ""),
        "text_output": st.session_state.get("last_text_output", ""),
    }
    history.insert(0, file_info)
    st.session_state["file_history"] = history[:10]

# 파일 히스토리 표시
if st.session_state["file_history"]:
   for idx, file_info in enumerate(st.session_state["file_history"]):
        file_name = Path(file_info["input"]).name
        progress_emoji = ""
        if file_info.get("text_output"):
            progress_emoji = "✅ 번역 완료"
        elif file_info.get("stt_output"):
            progress_emoji = "🎤 STT 완료"
        elif file_info.get("audio_output"):
            progress_emoji = "🔊 추출 완료"
        
        if st.sidebar.button(f"{file_name[:30] if len(file_name) > 30 else file_name} {progress_emoji}", key=f"history_{idx}"):
            # 세션 상태 업데이트 (모든 관련 키)
            st.session_state["audio_input_media_path"] = file_info["input"]
            
            # run_name 복원 (덮어쓰기 방지)
            run_name = sanitize_run_name(Path(file_info["input"]).stem)
            st.session_state["current_run_name"] = run_name
            
            if file_info.get("audio_output"):
                st.session_state["audio_output_path"] = file_info["audio_output"]
                st.session_state["stt_input_audio_path"] = file_info["audio_output"]
            if file_info.get("stt_output"):
                st.session_state["stt_output_path"] = file_info["stt_output"]
                st.session_state["last_stt_output"] = file_info["stt_output"]
                st.session_state["text_process_input_path"] = file_info["stt_output"]
            if file_info.get("text_output"):
                st.session_state["text_process_output_path"] = file_info["text_output"]
                st.session_state["last_text_output"] = file_info["text_output"]
            st.rerun()
else:
    st.sidebar.info("아직 작업한 파일이 없습니다")

st.sidebar.markdown("---")
st.sidebar.write("비동기 실행을 사용할 경우 Jobs 엔드포인트에서 상태를 추가로 확인할 수 있습니다.")
st.sidebar.info(
    "ℹ️ **속도 안내**\n\n"
    "현재 프로토타입은 매 요청마다 AI 모델을 새로 로딩하므로 "
    "단계별로 약 10~30초의 초기화 시간이 소요됩니다. "
    "(실제 서비스 배포 시에는 모델을 메모리에 상주시켜 즉각 반응하도록 최적화됩니다.)"
)
