# 모듈 실행 체크리스트

## 공통 준비
- `scripts/setup_env.ps1` 스크립트로 백엔드/프론트엔드 가상환경과 모듈 의존성을 설치합니다.
- 모델 및 체크포인트 경로가 각 모듈의 `config/settings.yaml`에 정확히 설정되어 있는지 확인합니다.
- 실행 전 `data/inputs`, `data/intermediates`, `data/outputs` 경로에 필요한 파일(또는 빈 디렉터리)이 준비되어 있는지 확인합니다.

## Audio Extractor
```powershell
# 예시
python modules/audio_extractor/run.py `
  --input data\inputs\source.mp4 `
  --output data\intermediates\source_audio.wav `
  --config modules\audio_extractor\config\settings.yaml
```
- 출력 WAV 샘플레이트/채널 정보를 로그에서 확인하고, 결과 파일 용량과 길이를 검증합니다.

## Whisper STT
```powershell
python modules/stt_whisper/run.py `
  --input data\intermediates\source_audio.wav `
  --output data\intermediates\stt_result.json `
  --config modules\stt_whisper\config\settings.yaml
```
- 실행 로그의 모델 로딩 위치와 디바이스(GPU/CPU)를 확인합니다.
- 결과 JSON의 `language`, `segments` 필드를 검증하고 텍스트 내용이 정상인지 확인합니다.

## Text Processor
```powershell
python modules/text_processor/run.py `
  --input data\intermediates\stt_result.json `
  --output data\intermediates\text_processed.json
```
- 전처리 결과의 `processed_text`가 의도대로 변환되었는지 확인합니다.

## VALL-E X TTS
```powershell
python modules/tts_vallex/run.py `
  --input data\intermediates\text_processed.json `
  --output data\intermediates\tts_output.wav `
  --config modules\tts_vallex\config\settings.yaml
```
- 로그에 출력된 실제 실행 명령을 확인하고, 생성된 WAV 파일을 재생하여 품질을 점검합니다.
- 필요 시 `command_template`와 환경 변수를 조정합니다.

## XTTS 백업
```powershell
python modules/tts_xtts/run.py `
  --input data\intermediates\text_processed.json `
  --output data\intermediates\tts_backup_output.wav `
  --config modules\tts_xtts\config\settings.yaml
```
- 참조 화자 음성이 필요한 경우 `speaker_wav` 경로를 설정하고 생성된 음성이 올바른지 확인합니다.

## RVC 음성 변환
```powershell
python modules/voice_conversion_rvc/run.py `
  --input data\intermediates\tts_output.wav `
  --output data\intermediates\rvc_output.wav `
  --config modules\voice_conversion_rvc\config\settings.yaml
```
- 출력 WAV의 길이와 레벨을 확인하고, 변환된 음색이 기대에 부합하는지 검증합니다.
- 외부 스크립트 인자가 누락되었는지 로그를 기반으로 재확인합니다.

## Wav2Lip 립싱크
```powershell
python modules/lipsync_wav2lip/run.py `
  --video data\inputs\source.mp4 `
  --audio data\intermediates\rvc_output.wav `
  --output data\outputs\final_dubbed.mp4 `
  --config modules\lipsync_wav2lip\config\settings.yaml
```
- 결과 영상의 입 모양과 오디오 동기화 상태를 육안으로 확인합니다.
- GPU 리소스 사용량이 적절한지 모니터링합니다.

## 오케스트레이터 실행
```powershell
powershell -ExecutionPolicy Bypass -File scripts/run_pipeline.ps1
```
- 각 단계 로그가 순차적으로 출력되는지 확인하고, 실패 시 `config.yaml`의 커맨드 인자를 재검토합니다.

## 로그 및 피드백 기록
- 각 모듈 실행 후 성공/실패 여부, 수정해야 할 인자 또는 경로를 기록합니다.
- 필요 시 `docs/module_run_checklist.md`에 항목을 추가하거나 주석을 보완합니다.
