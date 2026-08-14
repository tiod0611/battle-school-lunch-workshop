<#
  급식배틀 앱을 로컬에서 한 번에 실행하는 스크립트 (백엔드 + 프론트엔드).
  사전 준비: .env.example을 .env로 복사하고 NEIS_API_KEY를 입력해야 합니다.
  사용법: 프로젝트 루트에서 `./scripts/run-dev.ps1` 실행
#>

$ErrorActionPreference = "Stop"

# winget으로 설치된 Python/Node의 PATH가 새 프로세스에 즉시 반영되지 않는 경우를 대비해 갱신
$env:PATH = [System.Environment]::GetEnvironmentVariable("PATH", "Machine") + ";" + [System.Environment]::GetEnvironmentVariable("PATH", "User")

$root = Split-Path -Parent $PSScriptRoot

if (-not (Test-Path (Join-Path $root ".env"))) {
    Write-Warning ".env 파일이 없습니다. .env.example을 복사한 뒤 NEIS_API_KEY를 입력하세요."
}

Write-Host "백엔드(FastAPI, :8000)와 프론트엔드(Vite, :3000)를 새 창에서 각각 실행합니다..."

Start-Process powershell -ArgumentList @(
    "-NoExit", "-Command",
    "cd '$root\backend'; `$env:PATH = [System.Environment]::GetEnvironmentVariable('PATH','Machine') + ';' + [System.Environment]::GetEnvironmentVariable('PATH','User'); python -m uvicorn app.main:app --reload --port 8000"
)

Start-Process powershell -ArgumentList @(
    "-NoExit", "-Command",
    "cd '$root\frontend'; `$env:PATH = [System.Environment]::GetEnvironmentVariable('PATH','Machine') + ';' + [System.Environment]::GetEnvironmentVariable('PATH','User'); npm run dev"
)

Write-Host "두 서버가 각각 새 PowerShell 창에서 시작되었습니다. 창을 닫으면 서버가 종료됩니다."
