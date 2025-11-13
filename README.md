# Padiem RnD Modular Dubbing Pipeline

## 목적
더빙 파이프라인을 단계별 모듈로 분리하여 의존성 충돌을 최소화하고 유지보수성을 높이는 것을 목표로 합니다.

## 모듈 개요
1. Audio Extractor  
2. Whisper STT  
3. Text Processor / Translator  
4. VALL-E X TTS  
5. XTTS (백업 TTS)  
6. RVC Voice Conversion  
7. Wav2Lip LipSync  
8. Orchestrator (워크플로 제어)

## 데이터 IO 규칙
- 입력·중간·출력 파일은 `data/` 하위에 표준화된 형식(JSON, WAV, MP4 등)으로 저장합니다.
- 모든 모듈은 `shared/schemas`에 정의한 포맷을 따릅니다.

## 환경 및 의존성 가이드
- 모듈별로 `requirements.txt` 또는 `environment.yml`을 추가하여 독립적인 가상환경을 구성할 수 있습니다.
- GPU가 필요한 모듈(STT, TTS, RVC, Wav2Lip)은 CUDA 버전을 명시하고, CPU 전용 옵션도 주석으로 남겨 두는 것을 권장합니다.
- 백엔드/프론트엔드 의존성:
  ```powershell
  # 백엔드
  pip install -r backend/requirements.txt

  # 프론트엔드
  pip install -r frontend/requirements.txt
  ```
  가상환경을 분리하려면 `python -m venv .venv_backend`, `.venv_frontend` 등으로 각각 생성 후 활성화합니다.
- `scripts/setup_env.ps1`을 실행하면 백엔드/프론트엔드 가상환경이 자동으로 생성되고 모듈 의존성까지 설치됩니다.

## 오케스트레이션
- `orchestrator/config.yaml`에 모듈 실행 커맨드를 정의하고 `pipeline_runner.py`가 순차적으로 호출합니다.
- `scripts/run_pipeline.ps1`을 통해 백엔드 가상환경 내에서 전체 파이프라인을 실행할 수 있습니다.

## 백엔드 API 프로토타입
- `backend/` 디렉터리에 FastAPI 기반 프로토타입이 위치합니다.
- 실행 예시:
  ```powershell
  uvicorn backend.main:app --reload --port 8000
  ```
- 주요 엔드포인트:
  - `POST /audio/extract`
  - `POST /stt/`
  - `POST /text/process`
  - `POST /tts/`
  - `POST /tts-backup/`
  - `POST /rvc/`
  - `POST /lipsync/`

## Streamlit UI 프로토타입
- `frontend/app.py`를 실행하여 모듈 호출 플로우를 시각화할 수 있습니다.
- 실행 예시:
  ```powershell
  streamlit run frontend/app.py
  ```
- 사이드바에서 API 기본 URL을 설정한 뒤 각 모듈 섹션에서 경로와 설정 파일을 입력하고 실행합니다.
- 현재 모듈 로직은 TODO 상태이므로 실제 실행 시 `NotImplementedError`가 발생할 수 있으며, 플로우 검증용으로 사용합니다.

## 테스트 데이터 및 연동 시나리오
- `docs/sample_data_instructions.md`에서 샘플 데이터 구조와 오케스트레이터-API 연동 시나리오를 확인할 수 있습니다.
- 스모크 테스트 실행: `scripts/run_tests.ps1` (기본 `-m smoke`), CI와 연동 시 GPU 환경 여부를 고려하여 더미/모킹 기반 검증을 유지합니다.

## 실제 모델 연동 요약
- Whisper STT: `modules/stt_whisper/config/settings.yaml`에서 `large-v3` 모델과 캐시 경로 지정.
- VALL-E X TTS: `modules/tts_vallex/config/settings.yaml`을 통해 외부 스크립트/체크포인트 호출.
- XTTS 백업: `modules/tts_xtts/config/settings.yaml`에서 Coqui XTTS v2 설정 및 참조 음성 지정.
- RVC 변환: `modules/voice_conversion_rvc/config/settings.yaml`에서 실행 스크립트, 체크포인트, 파라미터 정의.
- Wav2Lip 립싱크: `modules/lipsync_wav2lip/config/settings.yaml`에 스크립트와 모델 경로 구성.
- 각 모듈은 설정 파일을 수정해 로컬 환경 경로나 옵션을 맞춘 뒤 `run.py`를 실행하거나 API를 통해 호출합니다.
