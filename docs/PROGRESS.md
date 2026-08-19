# 百战智能运营平台 — 开发进度报告

> 报告时间：2026-08-19 21:04
> 项目路径：`D:/ai agent学习/rag/bai-zhan-ai-platform/`
> GitHub：`https://github.com/alecemlurui/bai-zhan-ai-platform`
> 本报告不含任何 API Key / JWT Secret / 数据库凭证。

---

## 1. 项目概况

基于 FastAPI + Tortoise ORM + Aerich + Celery + Docker 的后端骨架，覆盖用户认证、主题/题目/文章生成、任务工作流、媒体/OSS、小红书发布、素材库等核心模块的最小可运行版本。当前已完成 **Phase 0 开发基线与一键脚本**，代码已推送 GitHub。

---

## 2. 当前完成度（按里程碑）

| 里程碑 | 状态 | 说明 |
| --- | --- | --- |
| A. 项目骨架与环境 | ✅ 完成 | Dockerfile、docker-compose、requirements、README、一键脚本已到位 |
| B. 数据库与 ORM | ✅ 完成 | Tortoise 模型、`aerich` 迁移、初始 schema 已提交 |
| C. 用户认证 | ✅ 完成 | 注册/登录/JWT/依赖注入，测试通过 |
| D. 基础 API | ✅ 完成 | Health、Topics、Titles、Articles、Publish 路由 |
| E. Agent / 任务流 | ✅ 完成 | `AgentRunner` + Celery worker + `Task` 状态机，可触发任务 |
| F. 媒体与素材 | ✅ 骨架完成 | Media / Materials / Publish API 已存在，待接真实 OSS / 小红书 SDK |
| G. 向量检索/RAG | ⏳ 未开始 | 需接入 Embedding + Chroma/FAISS/Weaviate |
| H. 前端示例 | ⏳ 未开始 | 仅提供 OpenAPI/Postman |
| I. 部署/监控 | ⏳ 未开始 | Docker 已提供，K8s/监控待补 |
| J. 代码质量与 CI | ✅ 基线完成 | black/isort/flake8/mypy/bandit 配置通过；ci_check 脚本可用 |

---

## 3. Phase 0 已完成工作（开发基线）

### 3.1 一键脚本

新增 `scripts/` 目录：

- `dev_up.sh` / `dev_up.ps1`：一键启动 Postgres、Redis、迁移、后端与 Worker。
- `ci_check.sh` / `ci_check.ps1`：一键运行 black / isort / flake8 / mypy / bandit / pytest。

### 3.2 质量工具配置

- `backend/requirements.txt`：新增 `black`、`isort`、`flake8`、`mypy`、`bandit`、`pre-commit`。
- `backend/pyproject.toml`：新增 `[tool.black]`、`[tool.isort]`、`[tool.mypy]` 配置。
- 项目根目录新增 `.flake8`：行宽 88，忽略 E203/W503，排除 `.venv` / `migrations`。

### 3.3 代码风格与类型修复

- 运行 `black backend/`、`isort backend/` 自动格式化全部源码。
- 修复 `flake8` 报错：
  - 补全 `backend/app/api/articles.py`、`backend/app/api/publish.py` 缺失的 `Task` 导入。
  - 删除 `backend/app/api/publish.py` 未使用的 `publish_article` 导入。
  - 修复 `backend/app/dependencies.py`、`backend/app/main.py` 的未使用导入。
  - 修正 `backend/app/services/agent_runner.py` 的 import 与状态枚举类型。
- 修复 `mypy` 报错：
  - 把 `agent_runner.py` 的字符串状态改为 `TaskStatus` / `ArticleStatus` 枚举。
  - 在 `topic.py` 为 Tortoise 关联字段访问添加 `# type: ignore[attr-defined]`。
  - 在 `backend/pyproject.toml` 禁用 `var-annotated` 与 `no-any-return` 以适配 Tortoise 动态属性。

### 3.4 验证结果

在项目根执行完整 CI 检查链：

```bash
set LLM_MOCK=true
set JWT_SECRET=test-secret
backend/.venv/Scripts/python.exe -m black --check backend
backend/.venv/Scripts/python.exe -m isort --check-only backend
backend/.venv/Scripts/python.exe -m flake8 backend
cd backend && .venv/Scripts/python.exe -m mypy . --ignore-missing-imports
backend/.venv/Scripts/python.exe -m bandit -r backend/app backend/tests -ll
backend/.venv/Scripts/python.exe -m pytest -q
```

结果：

```text
black: All done! 28 files would be left unchanged.
isort: Skipped 2 files
flake8: 无错误
mypy: Success: no issues found in 27 source files
bandit: No issues identified. Medium: 0, High: 0
pytest: 10 passed in ~9s
```

---

## 4. 已知阻塞与环境问题

| 问题 | 状态 | 说明 |
| --- | --- | --- |
| Docker Desktop 未运行 | ⚠️ 阻塞 | `docker-compose up -d postgres redis` 失败，错误 `open //./pipe/dockerDesktopLinuxEngine: The system cannot find the file specified.`。需用户手动启动 Docker Desktop 后再验证。 |

该阻塞不影响代码提交与 CI 检查；只影响本地容器化启动与集成测试中的真实 Postgres/Redis。

---

## 5. 代码提交与远程同步

- 本地提交：`9cb4046 feat(dev): Phase 0 dev baseline and one-click scripts`
- 已推送至：`git@github.com:alecemlurui/bai-zhan-ai-platform.git` 的 `main` 分支
- 变更文件：21 files changed, 293 insertions(+), 39 deletions(-)
- 未提交任何真实密钥；`.env` 已受 `.gitignore` 保护。

---

## 6. 关键文件结构

```text
bai-zhan-ai-platform/
├── .env.example                # 环境变量模板（仅占位符，无真实密钥）
├── .flake8                     # flake8 配置
├── .gitignore
├── docker-compose.yml
├── pytest.ini
├── README.md
├── .github/workflows/ci.yml
├── scripts/
│   ├── dev_up.sh               # Linux/WSL 一键启动
│   ├── dev_up.ps1              # Windows PowerShell 一键启动
│   ├── ci_check.sh             # Linux/WSL 一键质量检查
│   └── ci_check.ps1            # Windows PowerShell 一键质量检查
├── backend/
│   ├── Dockerfile
│   ├── requirements.txt
│   ├── pyproject.toml          # 含 black/isort/mypy 配置
│   ├── app/
│   │   ├── main.py             # FastAPI 入口 + lifespan
│   │   ├── config.py           # Pydantic Settings
│   │   ├── models.py           # Tortoise ORM 模型
│   │   ├── schemas.py          # Pydantic 请求/响应
│   │   ├── dependencies.py     # JWT 依赖
│   │   ├── router.py           # API 路由聚合
│   │   ├── api/                # 各模块路由
│   │   ├── services/           # 业务逻辑（auth、topic、agent、media、publish...）
│   │   ├── tasks.py            # Celery 任务
│   │   └── worker.py           # Celery worker 入口
│   ├── migrations/models/      # Aerich 初始迁移
│   └── tests/                  # pytest 用例
└── docs/
    └── PROGRESS.md             # 本报告
```

---

## 7. 主要技术决策

- **密码哈希**：弃用 `passlib+bcrypt`（bcrypt 5.0 与 passlib 1.7.4 不兼容），改用标准库 `hashlib.pbkdf2_hmac`。
- **JWT**：`sub` 声明使用字符串，避免 `python-jose` 的 `JWTClaimsError`。
- **测试数据库**：使用独立临时 SQLite 文件，避免 `:memory:` 跨 event loop 表丢失。
- **ASGI 测试客户端**：使用 `httpx.ASGITransport` 替代已废弃的 `AsyncClient(app=...)`。
- **Pydantic / Tortoise 弃用警告**：已迁移到 `ConfigDict`、`SettingsConfigDict`、`primary_key=True`。
- **LLM 默认 Mock**：当前 `LLM_MOCK=true` 可保证测试与无 Key 环境通过；真实接入时通过 `.env` 关闭 Mock。

---

## 8. 待完善项（按优先级）

| 序号 | 事项 | 优先级 | 所属阶段 |
| --- | --- | --- | --- |
| 1 | 接入真实 LLM API（DeepSeek / OpenAI / Coze），替换 `LLM_MOCK` | 高 | Phase 1 |
| 2 | 增强 LLM 客户端：重试、超时、token 计费、异常处理 | 高 | Phase 1 |
| 3 | 向量检索/RAG：Embedding + Chroma/FAISS + 文本分块 | 高 | Phase 2 |
| 4 | 图片生成、阿里云 OSS 上传、本地回退 | 中 | Phase 3 |
| 5 | 小红书账号绑定与发布 API（真实 SDK / mock） | 中 | Phase 3 |
| 6 | Celery + Redis 实际运行验证 | 中 | Phase 1/2 |
| 7 | 补充更多集成测试（生成文章全链路、发布链路） | 中 | 各阶段 |
| 8 | 前端最小示例或 Postman Collection | 低 | Phase 4 |
| 9 | K8s / Prometheus / Sentry 生产部署 | 低 | Phase 5 |

---

## 9. 下一步建议（Phase 1：真实 LLM 接入）

建议按以下顺序推进 Phase 1：

1. **增强 `backend/app/services/llm_client.py`**：
   - 添加 `httpx.AsyncClient` 超时与连接池配置。
   - 实现指数退避重试（max 3 次）。
   - 记录 token 使用量与估算费用到 task metadata。
   - 统一异常分类：`LLMRateLimitError`、`LLMTimeoutError`、`LLMContentFilterError`、`LLMUnknownError`。

2. **强化 `backend/app/services/agent_runner.py`**：
   - 为 `generate_titles` / `generate_article` 设计结构化 prompt 模板。
   - 添加 JSON 输出解析与失败 fallback。
   - 把检索上下文自动拼入 article prompt（预留 RAG 接口）。

3. **补充 `backend/tests/test_llm_integration.py`**：
   - Mock LLM HTTP 响应，验证重试、超时、异常处理。
   - 测试 `generate_titles` 在真实/Mock 模式下的输出格式。

4. **验证 Docker 启动**：
   - 用户启动 Docker Desktop 后，运行 `docker-compose up -d postgres redis` 与 `scripts/ci_check.ps1`。

### 需要用户提供

- 是否已启动 Docker Desktop？
- 是否有真实 LLM API Key，以及服务商（当前 `.env.example` 默认 DeepSeek）？

---

## 10. 安全与密钥说明

- 项目未提交任何真实密钥。
- `.env` 已在 `.gitignore` 中排除。
- 配置文件仅保留默认值/空字符串作为 fallback。
- 运行前请复制 `.env.example` → `.env` 并填入真实值。
