---
📅 **날짜**: 2024년 10월 17일 (목)
👤 **작성자**: 강철원 (연구책임자) | **승인**: 강혜림 (대표)
📊 **진행 단계**: 1단계 - 기초연구 및 설계
🎯 **주요 작업**: TTS 및 VC 기술 조사
---

# AI 기반 다국어 음성 합성 및 실시간 립싱크 더빙 시스템 개발일지

## 📋 오늘의 작업 내용

### 1. VALL-E X (TTS) 분석

- **특징**: 마이크로소프트 리서치에서 발표. 3초 분량의 음성 샘플만으로 목소리 복제 가능 (Zero-shot). 다국어 지원.
- **장점**: 교차 언어(Cross-lingual) 합성 가능 (예: 한국인 목소리로 영어 발화).
- **단점**: 공식 코드가 없거나 제한적. 오픈소스 구현체 확인 필요.

### 2. RVC (Voice Conversion) 분석

- **특징**: Retrieval-based Voice Conversion. 적은 데이터로도 고품질 음성 변환 가능.
- **활용**: VALL-E X로 생성된 음성의 톤을 원본 화자와 더욱 비슷하게 보정하는 용도로 사용 계획.

## 🔧 기술적 진행사항

### Strategy

- **Hybrid Approach**: VALL-E X로 1차 생성(발음, 언어 처리) -> RVC로 2차 보정(음색 강화).

## 📊 진행 상황

| 항목 | 계획 | 실제 | 상태 |
|------|------|------|------|
| VALL-E X 분석 | 완료 | 완료 | ✅ |
| RVC 분석 | 완료 | 완료 | ✅ |

## 🚧 이슈 사항 및 해결 방안

- **복잡도**: 두 모델을 연동하는 파이프라인 구성이 복잡할 수 있음. -> 단계별 구현 전략 수립.

## 📝 내일 계획

1. Wav2Lip 기술 조사
2. 10월 3주차 주간 정리

---

## 📚 참고 자료

- [1] "VALL-E X Paper". [Link](https://arxiv.org/abs/2303.03926)

<details>
<summary>IRIS 붙여넣기용 HTML 코드</summary>

```html
<h3>1. VALL-E X (TTS) 분석</h3>
<ul>
<li><strong>특징</strong>: 마이크로소프트 리서치에서 발표. 3초 분량의 음성 샘플만으로 목소리 복제 가능 (Zero-shot). 다국어 지원.</li>
<li><strong>장점</strong>: 교차 언어(Cross-lingual) 합성 가능 (예: 한국인 목소리로 영어 발화).</li>
<li><strong>단점</strong>: 공식 코드가 없거나 제한적. 오픈소스 구현체 확인 필요.</li>
</ul>
<h3>2. RVC (Voice Conversion) 분석</h3>
<ul>
<li><strong>특징</strong>: Retrieval-based Voice Conversion. 적은 데이터로도 고품질 음성 변환 가능.
<li><strong>활용</strong>: VALL-E X로 생성된 음성의 톤을 원본 화자와 더욱 비슷하게 보정하는 용도로 사용 계획.</li>
</ul>
```

</details>
