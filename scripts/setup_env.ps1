param(
    [string]$BackendEnv = ".venv_backend",
    [string]$FrontendEnv = ".venv_frontend",
    [switch]$Force
)

function Initialize-Venv {
    param(
        [string]$EnvPath,
        [string]$Requirements
    )

    if (Test-Path $EnvPath) {
        if (-not $Force) {
            Write-Host "환경 $EnvPath 가 이미 존재합니다. --Force 옵션으로 재생성 가능합니다." -ForegroundColor Yellow
            return
        }
        Remove-Item $EnvPath -Recurse -Force
    }

    python -m venv $EnvPath
    & "$EnvPath\Scripts\pip.exe" install --upgrade pip
    if (Test-Path $Requirements) {
        & "$EnvPath\Scripts\pip.exe" install -r $Requirements
    }
}

Write-Host "백엔드 가상환경 초기화..." -ForegroundColor Cyan
Initialize-Venv -EnvPath $BackendEnv -Requirements "backend/requirements.txt"

Write-Host "프론트엔드 가상환경 초기화..." -ForegroundColor Cyan
Initialize-Venv -EnvPath $FrontendEnv -Requirements "frontend/requirements.txt"

Write-Host "모듈별 의존성 설치..." -ForegroundColor Cyan
$moduleRequirements = @(
    "modules/tts_xtts/requirements.txt"
)
foreach ($req in $moduleRequirements) {
    if (Test-Path $req) {
        & "$BackendEnv\Scripts\pip.exe" install -r $req
    }
}

Write-Host "환경 구성이 완료되었습니다." -ForegroundColor Green
