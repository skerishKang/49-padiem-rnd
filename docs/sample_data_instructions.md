# 샘플 데이터 및 실행 시나리오

## 데이터 배치
- 오디오/영상 원본: `data/inputs/`
  - 예시: `data/inputs/source.mp4`
- 중간 산출물: `data/intermediates/`
  - STT 결과: `data/intermediates/stt_result.json`
  - 텍스트 처리 결과: `data/intermediates/text_processed.json`
  - 합성 음성: `data/intermediates/tts_output.wav`
  - 백업 TTS: `data/intermediates/tts_backup_output.wav`
  - RVC 결과: `data/intermediates/rvc_output.wav`
- 최종 결과: `data/outputs/`
  - 립싱크 완료 영상: `data/outputs/final_dubbed.mp4`

## 샘플 JSON 구조
STT 결과(`stt_result.json`) 예시:
```json
{
  "id": "example_audio",
  "segments": [
    {"id": 0, "start": 0.0, "end": 3.2, "text": "안녕하세요"},
    {"id": 1, "start": 3.2, "end": 6.5, "text": "테스트 음원입니다"}
  ]
}
```

텍스트 처리 결과(`text_processed.json`) 예시:
```json
{
  "id": "example_audio",
  "segments": [
    {
      "id": 0,
      "original_text": "안녕하세요",
      "processed_text": "안녕하세요",
      "start": 0.0,
      "end": 3.2
    },
    {
      "id": 1,
      "original_text": "테스트 음원입니다",
      "processed_text": "테스트 음원입니다",
      "start": 3.2,
      "end": 6.5
    }
  ]
}
```

## 오케스트레이터 ↔ API 연동 시나리오
1. **오디오 추출**
   - API: `POST /audio/extract`
   - 커맨드 예시: `python orchestrator/pipeline_runner.py` (config.yaml 사용) 또는 API 호출
2. **STT → 텍스트 처리 → TTS**
   - STT 결과를 `text_processor`에 입력
   - VALL-E X 합성과 XTTS 백업 합성 중 하나 선택 (혹은 둘 다 실행)
3. **RVC 변환 → 립싱크**
   - RVC 결과 WAV를 립싱크 모듈로 전달
4. **Orchestrator와 API 통합**
   - 단일 머신에서는 Orchestrator가 CLI를 호출하고, UI에서는 API를 호출하여 결과 비교
   - 향후 Orchestrator가 HTTP API를 호출하도록 확장 가능

## 테스트 단계 체크리스트
1. 샘플 MP4/WAV/JSON 파일 준비
2. 오케스트레이터 또는 UI를 통해 각 단계 실행
3. `backend/main.py`로 API 서버 실행, `frontend/app.py`로 UI 실행
4. 비동기 실행 옵션 테스트 후 `/jobs/{id}`로 상태 확인
5. 출력물 검증 후 필요 시 파라미터 조정
