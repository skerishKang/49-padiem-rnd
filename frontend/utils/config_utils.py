import yaml
import os
import re
import json
from pathlib import Path
import tempfile
import streamlit as st

def load_yaml_file(path):
    """YAML 파일을 로드하여 딕셔너리로 반환합니다."""
    try:
        with open(path, "r", encoding="utf-8") as f:
            return yaml.safe_load(f)
    except Exception as e:
        st.error(f"YAML 로드 오류 ({path}): {e}")
        return None

def write_yaml_file(path, data):
    """딕셔너리를 YAML 파일로 저장합니다."""
    try:
        with open(path, "w", encoding="utf-8") as f:
            yaml.dump(data, f, allow_unicode=True, default_flow_style=False)
        return True
    except Exception as e:
        st.error(f"YAML 저장 오류 ({path}): {e}")
        return False

def cleanup_temp_file(path):
    """임시 파일을 삭제합니다."""
    try:
        p = Path(path)
        if p.exists():
            p.unlink()
    except Exception:
        pass

def build_override_config(base_config_path, default_config_path, override_output_path, overrides):
    """
    기본 설정 파일(또는 사용자 지정 설정)을 로드하고,
    UI에서 입력받은 값(overrides)으로 덮어쓴 뒤 임시 YAML 파일을 생성합니다.
    """
    # 1. 기반이 될 설정 파일 결정
    if base_config_path:
        config_data = load_yaml_file(base_config_path)
    else:
        config_data = load_yaml_file(default_config_path)
    
    if config_data is None:
        return None

    # 2. 오버라이드 적용
    # overrides 딕셔너리의 키가 config_data에 있으면 덮어쓰기
    for key, value in overrides.items():
        config_data[key] = value
    
    # 3. 임시 파일로 저장
    if write_yaml_file(override_output_path, config_data):
        return str(override_output_path)
    else:
        return None

def sanitize_run_name(name):
    """실행 이름을 파일 시스템에 안전한 형태로 변환합니다."""
    # 영문, 숫자, 언더스코어, 하이픈만 허용, 공백은 언더스코어로
    s = re.sub(r'[^\w\s-]', '', name).strip().lower()
    return re.sub(r'[-\s]+', '_', s)

def update_run_defaults(input_path, exclude_keys=None):
    """
    입력 미디어 경로가 변경되면, 나머지 단계의 기본 파일명들을 자동으로 업데이트합니다.
    예: input.mp4 -> input_audio.wav, input_stt.json, ...
    """
    if not input_path:
        return

    p = Path(input_path)
    stem = p.stem
    base_dir = st.session_state.get("run_base_dir", "data/runs/sample")
    
    # 기본 디렉토리 생성
    Path(base_dir).mkdir(parents=True, exist_ok=True)
    intermediates_dir = Path(base_dir) / "intermediates"
    intermediates_dir.mkdir(exist_ok=True)
    outputs_dir = Path(base_dir) / "outputs"
    outputs_dir.mkdir(exist_ok=True)

    # 업데이트할 키와 포맷 정의
    defaults = {
        "audio_output_path": intermediates_dir / f"{stem}_audio.wav",
        "stt_input_audio_path": intermediates_dir / f"{stem}_audio.wav",
        "stt_output_path": intermediates_dir / f"{stem}_stt.json",
        "text_process_input_path": intermediates_dir / f"{stem}_stt.json",
        "text_process_output_path": intermediates_dir / f"{stem}_text.json",
        "tts_input_json_path": intermediates_dir / f"{stem}_text.json",
        "tts_output_path": intermediates_dir / f"{stem}_valle.wav",
        "xtts_input_json_path": intermediates_dir / f"{stem}_text.json",
        "xtts_output_path": intermediates_dir / f"{stem}_xtts.wav",
        "rvc_input_audio_path": intermediates_dir / f"{stem}_valle.wav", # 기본값은 VALL-E X
        "rvc_output_path": intermediates_dir / f"{stem}_rvc.wav",
        "lipsync_input_audio_path": intermediates_dir / f"{stem}_rvc.wav",
        "lipsync_output_path": outputs_dir / f"{stem}_dubbed.mp4",
    }
    
    # 입력이 비디오 파일인 경우에만 립싱크 입력 비디오 경로 업데이트
    video_extensions = {".mp4", ".mov", ".avi", ".mkv"}
    if p.suffix.lower() in video_extensions:
        defaults["lipsync_input_video_path"] = input_path

    for key, path in defaults.items():
        if exclude_keys and key in exclude_keys:
            continue
        # 사용자가 수동으로 수정한 적이 없거나, 강제 업데이트를 원할 경우 (여기선 단순화하여 항상 업데이트하되, 값이 비어있을때만 채우는 식은 아님)
        # Streamlit 특성상 위젯의 key와 연결된 session_state를 업데이트하면 위젯 값도 바뀜
        st.session_state[key] = str(path)

def update_output_path_from_input(input_path, output_key, suffix):
    """
    입력 파일 경로가 변경되었을 때, 출력 파일 경로를 자동으로 제안합니다.
    """
    if not input_path:
        return
    
    p = Path(input_path)
    stem = p.stem
    parent = p.parent # 보통 intermediates 폴더일 것임
    
    base_dir = st.session_state.get("run_base_dir", "data/runs/sample")
    target_dir = Path(base_dir) / "intermediates"
    if not target_dir.exists():
        target_dir = parent # fallback
        
    new_output = target_dir / f"{stem}{suffix}"
    
    # 현재 값과 다르면 업데이트
    if st.session_state.get(output_key) != str(new_output):
        st.session_state[output_key] = str(new_output)

def save_session_data(data):
    """세션 데이터를 JSON 파일로 저장합니다."""
    run_dir = st.session_state.get("run_base_dir")
    if not run_dir:
        return
        
    session_file = Path(run_dir) / "session.json"
    try:
        # 기존 데이터 로드
        current_data = {}
        if session_file.exists():
            with open(session_file, "r", encoding="utf-8") as f:
                current_data = json.load(f)
        
        # 업데이트
        current_data.update(data)
        
        with open(session_file, "w", encoding="utf-8") as f:
            json.dump(current_data, f, ensure_ascii=False, indent=2)
            
    except Exception as e:
        st.warning(f"세션 저장 실패: {e}")

def load_session_data(run_dir):
    """저장된 세션 데이터를 로드하여 st.session_state에 복원합니다."""
    session_file = Path(run_dir) / "session.json"
    if not session_file.exists():
        return
        
    try:
        with open(session_file, "r", encoding="utf-8") as f:
            data = json.load(f)
            
        for key, value in data.items():
            st.session_state[key] = value
            
    except Exception as e:
        st.warning(f"세션 로드 실패: {e}")
