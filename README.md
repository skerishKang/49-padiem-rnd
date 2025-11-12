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

## 오케스트레이션
- `orchestrator/config.yaml`에 모듈 실행 커맨드를 정의하고 `pipeline_runner.py`가 순차적으로 호출합니다.
