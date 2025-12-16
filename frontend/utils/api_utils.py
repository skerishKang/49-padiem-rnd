import os
import requests
import time
import json
import streamlit as st

# 기본값은 backend(uvicorn) 8000 포트로 맞추되, 필요 시 환경변수로 오버라이드
API_BASE_URL = os.getenv("PADIEM_API_BASE_URL", "http://localhost:8000")

def call_api(endpoint, method="POST", data=None, files=None):
    """백엔드 API를 호출하는 헬퍼 함수"""
    url = f"{API_BASE_URL}/{endpoint}"
    try:
        if method == "POST":
            response = requests.post(url, json=data, files=files)
        elif method == "GET":
            response = requests.get(url, params=data)
        
        response.raise_for_status()
        return response.json()
    except requests.exceptions.ConnectionError:
        st.error(f"백엔드 서버에 연결할 수 없습니다. ({url})")
        return None
    except requests.exceptions.HTTPError as e:
        st.error(f"API 오류 ({e.response.status_code}): {e.response.text}")
        return None
    except Exception as e:
        st.error(f"요청 중 오류 발생: {e}")
        return None

def get_job_status(job_id):
    """비동기 작업 상태를 조회합니다."""
    return call_api(f"jobs/{job_id}", method="GET")

def execute_step(endpoint, payload, async_mode=False):
    """
    각 단계의 실행을 담당하는 공통 함수.
    동기/비동기 모드를 지원하며, 상태 표시 및 에러 처리를 수행합니다.
    """
    if async_mode:
        # 비동기 실행 요청 (backend의 async_run 플래그 사용)
        async_payload = dict(payload)
        async_payload["async_run"] = True
        response = call_api(endpoint, data=async_payload)
        
        if response and "job_id" in response:
            job_id = response["job_id"]
            st.info(f"작업이 백그라운드에서 시작되었습니다. (Job ID: {job_id})")
            
            # 상태 폴링 UI
            status_placeholder = st.empty()
            progress_bar = st.progress(0)
            progress = 0
            
            while True:
                status = get_job_status(job_id)
                if not status:
                    break
                
                state = status.get("status")  # pending, running, success, failed
                error = status.get("error")
                
                if state == "success":
                    progress_bar.progress(100)
                    status_placeholder.success("완료되었습니다.")
                    return status.get("result", True)
                elif state == "failed":
                    status_placeholder.error(f"실패: {error or '알 수 없는 오류'}")
                    return None
                else:
                    label = "대기 중..." if state == "pending" else "실행 중..."
                    progress = min(progress + 5, 95)
                    progress_bar.progress(progress)
                    status_placeholder.info(f"{label} (상태: {state})")
                    time.sleep(2)  # 2초 간격 폴링
        return None
    else:
        # 동기 실행
        with st.spinner("작업 처리 중..."):
            response = call_api(endpoint, data=payload)
        
        if response:
            if response.get("status") == "success":
                st.success("완료되었습니다.")
                return response
            else:
                st.error("실패했습니다.")
        return None
