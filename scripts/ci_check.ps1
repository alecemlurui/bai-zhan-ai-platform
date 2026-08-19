# scripts/ci_check.ps1
# 本地 CI 检查（Windows PowerShell）

$ErrorActionPreference = "Stop"
$ProjectRoot = Resolve-Path (Join-Path $PSScriptRoot "..")
$BackendDir = Join-Path $ProjectRoot "backend"

& "$BackendDir\.venv\Scripts\Activate.ps1"

Write-Host "==> black --check backend/"
black --check "$BackendDir"
if ($LASTEXITCODE -ne 0) { throw "black check failed" }

Write-Host "==> isort --check-only backend/"
isort --check-only "$BackendDir"
if ($LASTEXITCODE -ne 0) { throw "isort check failed" }

Write-Host "==> flake8 backend/"
flake8 "$BackendDir"
if ($LASTEXITCODE -ne 0) { throw "flake8 failed" }

Write-Host "==> mypy backend/"
Set-Location $BackendDir
mypy . --ignore-missing-imports
if ($LASTEXITCODE -ne 0) { throw "mypy failed" }

Write-Host "==> bandit -r app tests/"
bandit -r app tests -ll -f json -o "$ProjectRoot\reports\bandit-report.json" || $true
bandit -r app tests -ll
if ($LASTEXITCODE -ne 0) { throw "bandit failed" }

Write-Host "==> pytest -q"
pytest -q
if ($LASTEXITCODE -ne 0) { throw "pytest failed" }

Write-Host ""
Write-Host "All checks passed."
