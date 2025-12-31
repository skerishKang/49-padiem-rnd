# 🎙️ AI 실시간 다국어 더빙 & 번역 하이브리드 파이프라인 (R&D)

본 리포지토리는 **(주)파디엠**과 **전북대학교 산학협력단**이 공동 수행한 'AI 기반 실시간 다국어 더빙 및 립싱크 기술 개발' 과제의 핵심 성과물과 최종 보고서를 포함하고 있습니다.

---

## 🏆 [핵심 성과] 최종 결과 보고서 (Main Report)

본 프로젝트의 모든 기술적 상세 설계, SOTA 알고리즘 비교 분석, 그리고 공인 기관 검증 결과는 아래의 **최종보고서 전문**에서 확인하실 수 있습니다.

### 📄 [최종보고서 전문 바로가기 (Full Report)](./최종보고서/본문12260102.md)

| 핵심 지표 (KPI) | 실측 성과 (Certified) | 판정 |
| :--- | :--- | :---: |
| **음성 인식 정확도 (WER)** | **3.62%** (목표 6.5% 이하) | **PASS** |
| **기계 번역 사명도 (BLEU)** | **43.87** (목표 41.0점 이상) | **PASS** |
| **음성 체감 품질 (MOS)** | **4.38** (목표 4.3점 이상) | **PASS** |
| **립싱크 화질 정밀도 (PSNR)** | **40.12dB** (목표 35.0dB 이상) | **PASS** |
| **시각적 자연스러움 (FID)** | **6.43** (목표 10.0 이하) | **PASS** |
| **다국어 지원 능력** | **5개 언어** (KO, EN, ZH, JA, ES) | **PASS** |
| **데이터셋 구축 규모** | **612.4GB** (목표 500GB 이상) | **PASS** |

---

## 🚀 프로젝트 개요 (Overview)

본 파이프라인은 영상 미디어의 글로벌 확산을 위해 STT, 번역, TTS, 그리고 립싱크 기술을 유기적으로 결합한 **엔드투엔드(End-to-End) 자동화 시스템**입니다. 각 단계를 모듈화하여 의존성 충돌을 최소화하고, 최신 SOTA 모델을 하이브리드로 활용하여 상용 서비스 수준의 품질을 확보했습니다.

### 🛠️ 핵심 기술 스택 (Technical Stack)
- **STT**: OpenAI Whisper (large-v3, medium) + TensorRT-LLM 최적화
- **Transcription/Translation**: GPT-4o & LLM 기반 맥락 인식 번역
- **TTS**: VALL-E X (Zero-shot Voice Cloning) + XTTS v2
- **LipSync**: MuseTalk & Wav2Lip (SOTA 기반 정밀 화질 구현)
- **Acceleration**: NVIDIA TensorRT, CUDA GPU 병렬 처리

---

## 📁 주요 모듈 및 파일 구조 (Structure)

- **`최종보고서/`**: [본문12260102.md](./최종보고서/본문12260102.md) 및 핵심 성과 시각화 이미지.
- **`modules/`**: STT, TTS, 번역, 립싱크 모듈별 독립 실행 스크립트.
- **`backend/`**: FastAPI 기반 비동기 파이프라인 오케스트레이터.
- **`frontend_unified/`**: Streamlit 기반 통합 제어 콘솔 UI.
- **`scripts/`**: 모델 계측(WER/BLEU/PSNR) 및 환경 구축 자동화 도구.

---

## ⚙️ 빠른 시작 (Quick Start)

### 1. 환경 설정
```powershell
# 가상환경 구축 및 의존성 일괄 설치
.\scripts\setup_env.ps1
```

### 2. 백엔드 실행
```powershell
uvicorn backend.main:app --reload --port 8000
```

### 3. 통합 제어 UI 실행
```powershell
streamlit run frontend_unified/Home.py
```

---

## 🎓 산학협력 (Academic Collaboration)
본 프로젝트는 **전북대학교 산학협력단**의 연구 인력 및 인프라 지원을 통해 기술적 무결성을 검증받았으며, 공인된 성능 지표 체계를 구축하였습니다.

---
© 2025 (주)파디엠 (PADIEM Co., Ltd.) All Rights Reserved.
