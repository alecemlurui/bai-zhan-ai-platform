#!/usr/bin/env bash
# scripts/dev_up.sh
# 一键启动开发环境（WSL / Linux / macOS）
# 用法：./scripts/dev_up.sh

set -e

PROJECT_ROOT="$(cd "$(dirname "$0")/.." && pwd)"
BACKEND_DIR="$PROJECT_ROOT/backend"

# 加载环境变量（如果 .env 存在）
if [ -f "$PROJECT_ROOT/.env" ]; then
    export $(grep -v '^#' "$PROJECT_ROOT/.env" | xargs)
fi

echo "==> 启动 Postgres / Redis 容器..."
docker-compose -f "$PROJECT_ROOT/docker-compose.yml" up -d postgres redis

echo "==> 等待 Postgres 就绪..."
for i in {1..30}; do
    if docker-compose -f "$PROJECT_ROOT/docker-compose.yml" exec -T postgres pg_isready -U postgres >/dev/null 2>&1; then
        echo "Postgres is ready"
        break
    fi
    sleep 1
done

echo "==> 创建/激活虚拟环境..."
if [ ! -d "$BACKEND_DIR/.venv" ]; then
    python3 -m venv "$BACKEND_DIR/.venv"
fi
source "$BACKEND_DIR/.venv/bin/activate"

echo "==> 安装依赖..."
pip install -r "$BACKEND_DIR/requirements.txt"

echo "==> 运行数据库迁移..."
cd "$BACKEND_DIR"
aerich upgrade || aerich init_db

echo "==> 启动 API 服务（后台）..."
nohup uvicorn app.main:app --reload --host 0.0.0.0 --port 8000 > "$PROJECT_ROOT/logs/uvicorn.log" 2>&1 &

echo "==> 启动 Celery Worker（后台）..."
nohup celery -A app.worker worker --loglevel=info > "$PROJECT_ROOT/logs/celery.log" 2>&1 &

echo ""
echo "开发环境已启动："
echo "  API:       http://localhost:8000"
echo "  文档:      http://localhost:8000/docs"
echo "  日志:      $PROJECT_ROOT/logs/"
echo ""
echo "停止服务： docker-compose -f $PROJECT_ROOT/docker-compose.yml down"
