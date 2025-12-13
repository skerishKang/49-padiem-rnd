---
📅 **날짜**: 2024년 10월 24일 (목)
👤 **작성자**: 강철원 (연구책임자) | **승인**: 강혜림 (대표)
📊 **진행 단계**: 1단계 - 기초연구 및 설계
🎯 **주요 작업**: 번역 기술 조사
---

# AI 기반 다국어 음성 합성 및 실시간 립싱크 더빙 시스템 개발일지

## 📋 오늘의 작업 내용

### 1. 번역 라이브러리 검토

- **Google Translate (Unofficial)**: `googletrans` 라이브러리. 무료지만 불안정함 (IP 차단 이슈).
- **Deep Translator**: 여러 번역 엔진(Google, Microsoft, DeepL 등)을 래핑한 라이브러리. -> `deep-translator` 채택.
- **Google Cloud Translation API**: 유료지만 가장 안정적이고 품질 좋음. -> 상용화 시 전환 고려.

### 2. 테스트

- 한국어 자막 -> 영어/일본어/중국어 번역 테스트.
- 문맥 유지 여부 확인.

## 🔧 기술적 진행사항

### Deep Translator

```python
from deep_translator import GoogleTranslator
translated = GoogleTranslator(source='ko', target='en').translate("안녕하세요")
```

## 📊 진행 상황

| 항목 | 계획 | 실제 | 상태 |
|------|------|------|------|
| 번역기 조사 | 완료 | 완료 | ✅ |
| 테스트 코드 | 완료 | 완료 | ✅ |

## 🚧 이슈 사항 및 해결 방안

- **줄바꿈**: 자막의 줄바꿈 문자가 번역 시 엉키는 문제. -> 전처리로 줄바꿈 제거 후 번역, 후처리로 다시 삽입하는 로직 필요.

## 📝 내일 계획

1. 10월 월간 보고서 작성
2. 11월 계획 수립

---

## 📚 참고 자료

- [1] "Deep Translator Docs".

<details>
<summary>IRIS 붙여넣기용 HTML 코드</summary>

```html
<h3>1. 번역 라이브러리 검토</h3>
<ul>
<li><strong>Google Translate (Unofficial)</strong>: <code>googletrans</code> 라이브러리. 무료지만 불안정함 (IP 차단 이슈).</li>
<li><strong>Deep Translator</strong>: 여러 번역 엔진(Google, Microsoft, DeepL 등)을 래핑한 라이브러리. -&gt; <code>deep-translator</code> 채택.</li>
<li><strong>Google Cloud Translation API</strong>: 유료지만 가장 안정적이고 품질 좋음. -&gt; 상용화 시 전환 고려.</li>
</ul>
<h3>2. 테스트</h3>
<ul>
<li>한국어 자막 -&gt; 영어/일본어/중국어 번역 테스트.</li>
<li>문맥 유지 여부 확인.</li>
</ul>
```

</details>
