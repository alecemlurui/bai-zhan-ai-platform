# scripts/dev_up.ps1
# 一键启动开发环境（Windows PowerShell）
# 用法：.\scripts\dev_up.ps1

$ErrorActionPreference = "Stop"
$ProjectRoot = Resolve-Path (Join-Path $PSScriptRoot "..")
$BackendDir = Join-Path $ProjectRoot "backend"

# 加载环境变量
$EnvFile = Join-Path $ProjectRoot ".env"
if (Test-Path $EnvFile) {
    Get-Content $EnvFile | ForEach-Object {
        if ($_ -match '^([^#][^=]*)=(.*)$') {
            [Environment]::SetEnvironmentVariable($matches[1], $matches[2], "Process")
        }
    }
}

Write-Host "==> 启动 Postgres / Redis 容器..."
docker-compose -f "$ProjectRoot\docker-compose.yml" up -d postgres redis

Write-Host "==> 等待 Postgres 就绪..."
for ($i = 1; $i -le 30; $i++) {
    try {
        docker-compose -f "$ProjectRoot\docker-compose.yml" exec -T postgres pg_isready -U postgres 2>$null | Out-Null
        Write-Host "Postgres is ready"
        break
    } catch {
        Start-Sleep -Seconds 1
    }
}

Write-Host "==> 创建/激活虚拟环境..."
$VenvDir = Join-Path $BackendDir ".venv"
if (-not (Test-Path $VenvDir)) {
    python -m venv $VenvDir
}
& "$VenvDir\Scripts\Activate.ps1"

Write-Host "==> 安装依赖..."
pip install -r "$BackendDir\requirements.txt"

Write-Host "==> 运行数据库迁移..."
Set-Location $BackendDir
aerich upgrade
if ($LASTEXITCODE -ne 0) {
    aerich init_db
}

Write-Host "==> 启动 API 服务（新窗口）..."
Start-Process powershell -ArgumentList "-NoExit", "-Command", "cd $BackendDir; uvicorn app.main:app --reload --host 0.0.0.0 --port 8000"

Write-Host "==> 启动 Celery Worker（新窗口）..."
Start-Process powershell -ArgumentList "-NoExit", "-Command", "cd $BackendDir; celery -A app.worker worker --loglevel=info"

Write-Host ""
Write-Host "开发环境已启动："
Write-Host "  API:       http://localhost:8000"
Write-Host "  文档:      http://localhost:8000/docs"
Write-Host ""
Write-Host "停止服务： docker-compose -f $ProjectRoot\docker-compose.yml down"
