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
- 파이프라인 실행 시 입력 미디어 파일명을 기준으로 `data/runs/{입력이름}/` 폴더가 생성되고, 단계별 산출물이 다음 규칙으로 저장됩니다.
  - `{입력이름}_audio.wav` : 오디오 추출 결과
  - `{입력이름}_result.json` : STT 원본 결과
  - `{입력이름}_text.json` : 텍스트 처리 결과
  - `{입력이름}_valle.wav` : VALL-E X 합성 결과
  - `{입력이름}_xtts.wav` : XTTS 백업 합성 결과
  - `{입력이름}_rvc.wav` : RVC 음성 변환 결과
  - `{입력이름}_wav2lip.mp4` : Wav2Lip 립싱크 결과
  - 위 경로들은 UI 및 오케스트레이터에서 자동 제안되지만 필요 시 수동으로 변경할 수 있습니다.

## 환경 및 의존성 가이드
- 루트에서 `python -m venv .venv_backend`, `python -m venv .venv_frontend`를 생성해 백엔드/프론트엔드 환경을 분리합니다.
- 각 디렉터리의 `requirements.txt`는 다음과 같습니다.
  - `backend/requirements.txt` : FastAPI, Uvicorn, Pydantic, PyYAML
  - `frontend/requirements.txt` : Streamlit, requests
- 의존성 설치 예시:
  ```powershell
  # 백엔드 환경 예시
  .\.venv_backend\Scripts\activate
  pip install -r backend/requirements.txt

  # 프론트엔드 환경 예시
  .\.venv_frontend\Scripts\activate
  pip install -r frontend/requirements.txt
  ```
- `scripts/setup_env.ps1`을 실행하면 위 과정을 일괄 처리하여 가상환경 생성 및 requirements 설치를 자동화합니다.
- GPU가 필요한 모듈(STT, TTS, RVC, Wav2Lip)은 CUDA 버전을 명시하고 CPU 전용 옵션도 주석으로 남겨 두는 것을 권장합니다.

## 오케스트레이션
- `orchestrator/config.yaml`은 `{input_media}`, `{audio_output}` 같은 플레이스홀더를 사용해 모듈 호출 명령을 템플릿으로 정의합니다.
- `pipeline_runner.py`는 입력 미디어 경로를 받아 실행 폴더와 산출물 이름을 자동으로 계산한 뒤, 템플릿을 실제 명령으로 매핑하여 순차 실행합니다.
- 실행 예시:
  ```powershell
  # 기본 설정 (입력 파일명 기반으로 data/runs/{stem}/에 결과 저장)
  python orchestrator/pipeline_runner.py --input-media data/inputs/sample.mp4

  # 실행 폴더명을 수동 지정하고, 화자 음성까지 제공하는 경우
  python orchestrator/pipeline_runner.py `
      --input-media data/inputs/sample.mp4 `
      --run-name sample_run `
      --run-root data/runs `
      --speaker-audio data/reference/speaker.wav
  ```
- PowerShell 스크립트를 사용할 수도 있습니다.
  ```powershell
  # venv 내 파이프라인 실행
  scripts/run_pipeline.ps1 `
      -InputMedia data/inputs/sample.mp4 `
      -RunName sample_run `
      -RunRoot data/runs `
      -SpeakerAudio data/reference/speaker.wav
  ```

## 텍스트 처리/번역 규칙
- `modules/text_processor/run.py`는 세그먼트별 타임스탬프와 음절 수를 기반으로 번역 길이를 맞춥니다.
- 기본 설정은 `modules/text_processor/config/settings.yaml`에서 관리하며, 주요 항목은 다음과 같습니다.
  - `source_language`, `target_language`
  - `syllable_tolerance` : 원본 대비 허용 비율(기본 10%)
  - `enforce_timing` : 길이 편차가 허용 범위를 넘으면 `needs_review` 플래그 표시
- 립싱크 정확도를 위한 전체 스키마와 규칙은 `docs/timed_translation_spec.md`에서 확인할 수 있습니다.

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

## 정적 웹 콘솔 (HTML/CSS/Vanilla JS)
- Streamlit과 별도로, `frontend/web/` 폴더에 순수 HTML/CSS/JS 기반 콘솔을 제공합니다.
- 실행 방법:
  1. FastAPI 백엔드를 먼저 기동합니다.
     ```powershell
     uvicorn backend.main:app --reload --port 8000
     ```
  2. `frontend/web/index.html` 파일을 브라우저에서 직접 열거나, 필요 시 간단한 정적 서버를 띄웁니다.
     ```powershell
     cd frontend/web
     python -m http.server 8501
     # 브라우저에서 http://localhost:8501 접속
     ```
- 좌측 사이드바에서 API 기본 URL, 폴링 간격, 최대 폴링 횟수를 설정하면 됩니다. 기본값은 `http://localhost:8000`.
- 각 단계 카드는 스트림릿과 동일한 엔드포인트(`/audio/extract`, `/stt/`, `/text/process`, `/tts/`, `/tts-backup/`, `/rvc/`, `/lipsync/`)를 호출하며, `fetch()`로 직접 JSON 요청을 보냅니다.
- "비동기 실행" 체크 시 `payload.async_run = true`로 요청하며, 응답에 `job_id`가 오면 `/jobs/{job_id}`를 주기적으로 폴링하여 상태를 로그 영역에 표시합니다.
- 하단 `응답 / 로그` 패널에서 모든 API 요청/응답을 확인할 수 있습니다.

-## 테스트 및 연동 시나리오
- `docs/sample_data_instructions.md`에서 샘플 데이터 구조와 오케스트레이터-API 연동 시나리오를 확인할 수 있습니다.
- 스모크 테스트 실행: `scripts/run_tests.ps1 -m smoke`
  - `-m all` 옵션을 주면 통합 모듈 검증을 수행합니다.
  - PowerShell 대신 Python으로 직접 실행하려면 `python -m pytest tests`를 사용할 수 있습니다.
- 모듈별 세부 체크리스트는 `docs/module_run_checklist.md`에 정리되어 있으니, 파이프라인에 새 모듈을 추가할 때 참고하세요.
- 립싱크 정확도를 위한 타임스탬프/음절 맞춤 번역 규격은 `docs/timed_translation_spec.md`에서 확인할 수 있습니다.

## 실제 모델 연동 요약
- Whisper STT: `modules/stt_whisper/config/settings.yaml`에서 `large-v3` 모델과 캐시 경로 지정.
- VALL-E X TTS: `modules/tts_vallex/config/settings.yaml`을 통해 외부 스크립트/체크포인트 호출.
- XTTS 백업: `modules/tts_xtts/config/settings.yaml`에서 Coqui XTTS v2 설정 및 참조 음성 지정.
- RVC 변환: `modules/voice_conversion_rvc/config/settings.yaml`에서 실행 스크립트, 체크포인트, 파라미터 정의.
- Wav2Lip 립싱크: `modules/lipsync_wav2lip/config/settings.yaml`에 스크립트와 모델 경로 구성.
- 각 모듈은 설정 파일을 수정해 로컬 환경 경로나 옵션을 맞춘 뒤 `run.py`를 실행하거나 API를 통해 호출합니다.
