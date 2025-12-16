import streamlit as st
import pandas as pd
import json
import os
from pathlib import Path

def build_theme_assets():
    """커스텀 CSS 및 테마 자산을 로드합니다."""
    st.markdown("""
        <style>
        .stApp {
            background-color: #0e1117;
        }
        .stButton>button {
            width: 100%;
            border-radius: 5px;
            height: 3em;
            font-weight: bold;
        }
        .stExpander {
            border: 1px solid #303030;
            border-radius: 5px;
            margin-bottom: 10px;
        }
        .block-container {
            padding-top: 2rem;
            padding-bottom: 5rem;
        }
        /* 사이드바 스타일 */
        [data-testid="stSidebar"] {
            background-color: #161b22;
            border-right: 1px solid #303030;
        }
        </style>
    """, unsafe_allow_html=True)

def format_timestamp(seconds):
    """초 단위 시간을 MM:SS.mmm 형식으로 변환합니다."""
    m, s = divmod(seconds, 60)
    return f"{int(m):02d}:{s:06.3f}"

def display_text_summary(json_path):
    """텍스트 처리 결과 요약을 표시합니다."""
    try:
        with open(json_path, "r", encoding="utf-8") as f:
            data = json.load(f)
        
        # text_processor 출력은 {"segments": [...]} 구조를 사용
        segments = data.get("segments") if isinstance(data, dict) else None
        if segments is None:
            # 혹시 상위가 바로 리스트인 경우도 지원
            if isinstance(data, list):
                segments = data
            else:
                st.warning("텍스트 처리 결과 형식을 인식할 수 없습니다.")
                return

        if not segments:
            st.warning("처리된 텍스트 세그먼트가 없습니다.")
            return

        df = pd.DataFrame(segments)

        # 원본/번역 컬럼 이름 매핑 (text_processor: original_text / processed_text)
        original_col = None
        translated_col = None
        if "original_text" in df.columns:
            original_col = "original_text"
        elif "text" in df.columns:
            original_col = "text"

        if "processed_text" in df.columns:
            translated_col = "processed_text"
        elif "translated_text" in df.columns:
            translated_col = "translated_text"

        # STT 뷰와 동일하게 시작/종료 시간을 포맷팅
        df["start_fmt"] = df["start"].apply(format_timestamp)
        df["end_fmt"] = df["end"].apply(format_timestamp)

        display_cols = [c for c in ["id", "start_fmt", "end_fmt", original_col, translated_col] if c]

        column_config = {
            "start_fmt": st.column_config.TextColumn("시작", width="small"),
            "end_fmt": st.column_config.TextColumn("종료", width="small"),
        }
        if original_col:
            column_config[original_col] = "원본 텍스트"
        if translated_col:
            column_config[translated_col] = "번역/처리 텍스트"

        st.dataframe(
            df[display_cols],
            use_container_width=True,
            hide_index=True,
            column_config=column_config,
        )
    except Exception as e:
        st.error(f"결과 요약 로드 실패: {e}")

def display_stt_result(json_path):
    """STT 결과를 데이터프레임으로 표시합니다."""
    try:
        with open(json_path, "r", encoding="utf-8") as f:
            data = json.load(f)
        
        # Whisper STT 출력은 {"segments": [...]} 구조, Gemini STT 출력은 리스트 루트일 수 있음
        if isinstance(data, dict):
            segments = data.get("segments", [])
        elif isinstance(data, list):
            segments = data
        else:
            segments = []

        if not segments:
            st.info("감지된 음성 구간이 없습니다.")
            return

        # 데이터프레임 변환
        df = pd.DataFrame(segments)

        # 일부 출력(JSON 리스트)에는 id 컬럼이 없을 수 있으므로 자동 생성
        if "id" not in df.columns:
            df["id"] = range(len(df))
        
        # 타임스탬프 포맷팅
        df["start_fmt"] = df["start"].apply(format_timestamp)
        df["end_fmt"] = df["end"].apply(format_timestamp)
        
        # 표시할 컬럼 선택
        display_df = df[["id", "start_fmt", "end_fmt", "text"]]
        
        st.dataframe(
            display_df,
            use_container_width=True,
            hide_index=True,
            column_config={
                "id": st.column_config.NumberColumn("ID", width="small"),
                "start_fmt": st.column_config.TextColumn("시작", width="small"),
                "end_fmt": st.column_config.TextColumn("종료", width="small"),
                "text": st.column_config.TextColumn("인식된 텍스트", width="large"),
            }
        )
        
        # 전체 텍스트 다운로드 버튼
        full_text = "\n".join([s.get("text", "") for s in segments])
        st.download_button(
            "전체 텍스트 다운로드 (TXT)",
            full_text,
            file_name=f"{Path(json_path).stem}.txt",
            mime="text/plain"
        )

    except Exception as e:
        st.error(f"STT 결과 로드 오류: {e}")

def text_input_with_state(label, key, default_value, help_text=None):
    """
    Session State와 연동되는 Text Input 헬퍼.
    값이 변경되면 Session State도 업데이트됩니다.
    """
    if key not in st.session_state:
        st.session_state[key] = default_value
    
    return st.text_input(label, value=st.session_state[key], key=key, help=help_text)

def handle_file_input(label, key, default_path, upload_label, allowed_extensions):
    """
    파일 경로 입력과 업로더를 결합한 컴포넌트.
    업로드된 파일이 있으면 자동으로 경로를 업데이트합니다.
    """
    # 1. 논리적 state key와 위젯 key를 분리한다.
    #    - state_key: 파이프라인에서 참조하는 세션 키 (예: "audio_input_media_path")
    #    - widget_key: 실제 Streamlit 위젯에 사용하는 키 (충돌 방지를 위해 별도)
    state_key = key
    widget_key = f"{key}_text"
    
    # 2. 현재 값 결정 (세션 상태가 있으면 사용, 없으면 기본값)
    path_value = st.session_state.get(state_key, default_path)
    
    # 3. 파일 업로더 (업로드 시 로컬 값만 갱신)
    uploaded_file = st.file_uploader(upload_label, type=allowed_extensions, key=f"{key}_uploader")
    
    if uploaded_file is not None:
        # 업로드된 파일을 data/inputs (또는 적절한 위치)에 저장
        # 여기서는 간단히 data/inputs 를 기본으로 함
        save_dir = Path("data/inputs")
        save_dir.mkdir(parents=True, exist_ok=True)
        
        file_path = save_dir / uploaded_file.name
        with open(file_path, "wb") as f:
            f.write(uploaded_file.getbuffer())
        
        path_value = str(file_path)
    
    # 4. 텍스트 입력을 렌더링 (위젯 key는 widget_key 사용)
    path_input = st.text_input(label, value=path_value, key=widget_key)
    
    # 5. 논리적 state_key와 동기화 (widget_key와는 별개로 유지)
    if path_input != st.session_state.get(state_key):
        st.session_state[state_key] = path_input
    
    return path_input
