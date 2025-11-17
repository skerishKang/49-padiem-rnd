# 타임스탬프 기반 음절 맞춤 번역 사양

Whisper STT → 텍스트 처리/번역 → TTS → Wav2Lip 립싱크 단계에서 각 세그먼트의 길이와 음절 수를 유지하기 위한 공통 규격입니다.

## 세그먼트 구조
```json
{
  "id": 0,
  "start": 1.25,
  "end": 3.80,
  "duration": 2.55,
  "original_text": "안녕하세요, 만나서 반갑습니다.",
  "source_language": "ko",
  "source_syllables": 11,
  "target_text": "Hello, nice to meet you.",
  "target_language": "en",
  "target_syllables": 11,
  "syllable_ratio": 1.0,
  "needs_review": false,
  "notes": null
}
```

## 처리 규칙
1. **STT 단계**
   - `segments[].start`, `segments[].end`, `segments[].text`를 포함한 JSON을 출력합니다.
   - Whisper 실행 시 `word_timestamps=True` 옵션을 사용하면 세그먼트 품질을 높일 수 있습니다.
2. **텍스트 처리/번역 단계**
   - 각 세그먼트에 대해 `source_syllables`, `target_text`, `target_syllables`, `syllable_ratio`를 계산합니다.
   - `syllable_ratio`가 `1 ± tolerance` 범위를 벗어나면 `needs_review=true`로 표시하여 후속 수동 조정을 요청합니다.
   - `target_text`는 LLM(예: Gemini) 결과나 번역 사전을 사용해 채웁니다.
3. **TTS 단계**
   - `duration`과 `target_syllables` 정보를 활용해 time-stretch, pause 삽입 등의 방식으로 원본 길이에 맞게 합성합니다.
4. **립싱크 단계**
   - Wav2Lip에는 `target_text`와 동일한 자막 혹은 phoneme 시퀀스를 제공하여 입 모양과 타이밍을 일치시킵니다.

## 구성 옵션
`modules/text_processor/config/settings.yaml` 예시:
```yaml
target_language: en
syllable_tolerance: 0.1   # ±10%
enforce_timing: true
operations:
  - trim
  - collapse_whitespace
```

- `target_language` : syllable estimator에 전달할 언어 코드
- `syllable_tolerance` : 원본 대비 허용 비율(0.1 → 10%)
- `enforce_timing` : 허용 범위를 벗어날 경우 경고 플래그를 세팅할지 여부

## 산출물 예시
```json
{
  "id": "sample_clip",
  "processed_at": "2025-11-17T02:05:00Z",
  "segments": [
    {
      "id": 0,
      "start": 0.0,
      "end": 2.4,
      "duration": 2.4,
      "original_text": "안녕하세요",
      "source_syllables": 5,
      "target_text": "Hello there",
      "target_syllables": 4,
      "syllable_ratio": 0.8,
      "needs_review": true,
      "notes": "syllable deficit"
    }
  ],
  "metadata": {
    "operation_sequence": ["trim", "collapse_whitespace"],
    "segment_count": 1,
    "syllable_tolerance": 0.1,
    "target_language": "en"
  }
}
```

이 규격을 준수하면 번역-합성 단계에서 길이 차이로 인한 립싱크 오류를 최소화할 수 있습니다.
