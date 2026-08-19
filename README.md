# 百战智能运营平台

企业级智能运营后端服务，支持主题生成、标题创作、文章生成、图片上传、素材库管理与第三方发布。

## 技术栈

- **Backend**: FastAPI + Pydantic v2
- **ORM**: Tortoise ORM + Aerich
- **任务队列**: Celery + Redis
- **认证**: JWT + PBKDF2-HMAC（标准库，无 bcrypt/passlib 依赖）
- **LLM**: OpenAI / Coze 兼容接口（支持 mock）
- **存储**: 本地文件 / 阿里云 OSS（预留）
- **容器**: Docker + docker-compose
- **测试**: pytest + httpx

## 目录结构

```text
.
├── .env.example
├── docker-compose.yml
├── backend/
│   ├── app/
│   │   ├── main.py
│   │   ├── config.py
│   │   ├── models.py
│   │   ├── schemas.py
│   │   ├── dependencies.py
│   │   ├── router.py
│   │   ├── worker.py
│   │   ├── tasks.py
│   │   ├── api/
│   │   │   ├── auth.py
│   │   │   ├── health.py
│   │   │   ├── topics.py
│   │   │   ├── titles.py
│   │   │   ├── articles.py
│   │   │   ├── media.py
│   │   │   ├── materials.py
│   │   │   └── publish.py
│   │   └── services/
│   │       ├── auth.py
│   │       ├── topic.py
│   │       ├── llm_client.py
│   │       ├── agent_runner.py
│   │       ├── media.py
│   │       └── publisher.py
│   ├── tests/
│   ├── migrations/
│   ├── requirements.txt
│   ├── Dockerfile
│   └── pyproject.toml
├── scripts/
│   ├── dev_up.sh / dev_up.ps1
│   └── ci_check.sh / ci_check.ps1
└── .github/workflows/ci.yml
```

## 快速开始

### 1. 环境变量

```bash
cp .env.example .env
# 编辑 .env 填入 JWT_SECRET 与 LLM_API_KEY
```

### 2. 一键启动开发环境（推荐）

```bash
# Linux / macOS / WSL
./scripts/dev_up.sh

# Windows PowerShell
.\scripts\dev_up.ps1
```

> 前置条件：Docker Desktop 已启动，.env 已配置。

### 3. 本地开发

```bash
cd backend
python -m venv .venv
.venv\Scripts\activate  # Windows
source .venv/bin/activate  # Linux/macOS

pip install -r requirements.txt

# 初始化/升级数据库
aerich upgrade

# 启动 API
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

### 4. 启动 Celery Worker

```bash
cd backend
celery -A app.worker worker --loglevel=info
```

### 5. Docker 一键启动

```bash
docker-compose up --build
```

### 6. 运行测试

```bash
cd backend
pytest -q
```

### 7. 本地 CI 检查

```bash
# Linux / macOS / WSL
./scripts/ci_check.sh

# Windows PowerShell
.\scripts\ci_check.ps1
```

检查项：black / isort / flake8 / mypy / bandit / pytest。

## 核心 API

| 方法 | 路径 | 说明 |
|---|---|---|
| POST | `/api/v1/auth/register` | 注册 |
| POST | `/api/v1/auth/login` | 登录 |
| GET | `/api/v1/auth/me` | 当前用户 |
| POST | `/api/v1/topics` | 创建主题 |
| GET | `/api/v1/topics` | 主题列表 |
| POST | `/api/v1/topics/{id}/generate-titles` | 生成标题 |
| GET | `/api/v1/topics/{id}/titles` | 标题列表 |
| POST | `/api/v1/articles/generate` | 生成文章 |
| POST | `/api/v1/media/upload` | 上传图片 |
| GET/POST/DELETE | `/api/v1/materials` | 素材库 |
| POST | `/api/v1/publish` | 发布文章 |

完整接口文档启动后访问：`http://localhost:8000/docs`

## 环境变量

| 变量 | 说明 |
|---|---|
| `DATABASE_URL` | 数据库 URL，默认 SQLite |
| `REDIS_URL` | Redis URL |
| `JWT_SECRET` | JWT 密钥 |
| `LLM_API_KEY` | LLM API Key |
| `LLM_BASE_URL` | LLM Base URL |
| `LLM_MODEL` | LLM 模型名 |
| `LLM_MOCK` | 是否启用 mock |
| `OSS_*` | 阿里云 OSS 配置（可选） |

## 部署

```bash
docker build -t bai-zhan-platform:latest ./backend
docker run -p 8000:8000 --env-file .env bai-zhan-platform:latest
```

## 后续扩展

- 接入真实 LLM（Coze / DeepSeek / OpenAI）
- 接入向量库（RAG）
- 小红书真实 API 发布
- 前端 React 管理后台
- Prometheus + Grafana 监控
