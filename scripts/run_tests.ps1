param(
    [string]$BackendEnv = ".venv_backend",
    [string]$Marker = "smoke"
)

$pytestExe = Join-Path $BackendEnv "Scripts\pytest.exe"
if (-not (Test-Path $pytestExe)) {
    Write-Host "백엔드 가상환경을 먼저 생성하세요. (scripts/setup_env.ps1 참고)" -ForegroundColor Red
    exit 1
}

& $pytestExe -m $Marker
