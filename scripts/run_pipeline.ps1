param(
    [string]$BackendEnv = ".venv_backend",
    [string]$ConfigPath = "orchestrator/config.yaml",
    [string]$InputMedia = "data/inputs/source.mp4",
    [string]$RunName = "",
    [string]$RunRoot = "data/runs",
    [string]$SpeakerAudio = ""
)

$pythonExe = Join-Path $BackendEnv "Scripts\python.exe"
if (-not (Test-Path $pythonExe)) {
    Write-Host "백엔드 가상환경을 먼저 생성하세요. (scripts/setup_env.ps1 참고)" -ForegroundColor Red
    exit 1
}

& $pythonExe "orchestrator/pipeline_runner.py" --config $ConfigPath --input-media $InputMedia --run-root $RunRoot @(
    if ($RunName) {"--run-name"; $RunName }
    if ($SpeakerAudio) {"--speaker-audio"; $SpeakerAudio }
)
