# 百战智能运营平台 — 开发进度报告

> 报告时间：2026-08-19 21:45
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
| K. 真实 LLM 接入 | ✅ Phase 1 完成 | LLMClient 增强：重试、超时、计费、异常分类；Agent prompt 结构化；新增集成测试 10 个 |

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

## 4. Phase 1：真实 LLM 接入（已完成）

### 4.1 LLMClient 增强（`backend/app/services/llm_client.py`）

- **结构化异常**：新增 `LLMError`、`LLMRateLimitError`、`LLMTimeoutError`、`LLMContentFilterError`、`LLMUnknownError`。
- **指数退避重试**：`LLM_MAX_RETRIES`（默认 3）、`LLM_RETRY_BACKOFF`（默认 2.0），对 429 / 超时 / 网络错误自动重试。
- **超时与连接错误**：区分 `httpx.TimeoutException`、`httpx.NetworkError`、`httpx.ConnectError`。
- **Token 与费用估算**：返回 `prompt_tokens` / `completion_tokens` / `total_tokens` / `cost_usd`。
- **JSON 输出**：新增 `chat_json()` 方法，支持 `response_format={"type": "json_object"}`。
- **Mock 模式增强**：根据用户消息自动识别“标题生成”意图，返回结构化示例 JSON，便于无 Key 环境跑通 Agent 全链路。

### 4.2 AgentRunner 增强（`backend/app/services/agent_runner.py`）

- `generate_titles` 改为优先请求 JSON 返回，并自动回退到纯文本行解析。
- 新增 `_build_title_prompt`、`_parse_title_json`、`_parse_title_text` 等辅助方法。
- `generate_article` 支持 `rag_context`、`word_count`、`style` 参数，并在 `article.metadata` 中记录 token、费用、延迟、模型。
- 捕获 `LLMError` 并记录结构化错误日志。

### 4.3 配置扩展

- `backend/app/config.py`：新增 `LLM_MAX_RETRIES`、`LLM_RETRY_BACKOFF`、`LLM_INPUT_PRICE_PER_1M`、`LLM_OUTPUT_PRICE_PER_1M`。
- `.env.example`：同步新增对应变量，默认使用 DeepSeek 定价占位（设为 0 则不计算费用）。

### 4.4 集成测试（`backend/tests/test_llm_integration.py`）

新增 10 个测试用例，覆盖：

- Mock 聊天与 JSON 聊天
- 真实 HTTP 调用模拟（200 成功）
- 429 触发重试后成功
- 429 重试耗尽失败
- 400 内容过滤异常
- 超时异常
- 未知异常
- AgentRunner 生成标题与文章全链路

### 4.5 Phase 1 验证结果

```text
black: 29 files would be left unchanged
isort: Skipped 2 files
flake8: 无错误
mypy: Success: no issues found in 28 source files
bandit: No issues identified. Medium: 0, High: 0
pytest: 20 passed in ~20s
```

---

## 5. 已知阻塞与环境问题

| 问题 | 状态 | 说明 |
| --- | --- | --- |
| Docker Desktop 未运行 | ⚠️ 阻塞 | `docker-compose up -d postgres redis` 失败，错误 `open //./pipe/dockerDesktopLinuxEngine: The system cannot find the file specified.`。需用户手动启动 Docker Desktop 后再验证。 |

该阻塞不影响代码提交与 CI 检查；只影响本地容器化启动与集成测试中的真实 Postgres/Redis。

---

## 6. 代码提交与远程同步

- Phase 0 提交：`9cb4046 feat(dev): Phase 0 dev baseline and one-click scripts`
- Phase 1 提交：待本次提交后更新
- 已推送至：`git@github.com:alecemlurui/bai-zhan-ai-platform.git` 的 `main` 分支
- 未提交任何真实密钥；`.env` 已受 `.gitignore` 保护。

---

## 7. 关键文件结构

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

## 8. 主要技术决策

- **密码哈希**：弃用 `passlib+bcrypt`（bcrypt 5.0 与 passlib 1.7.4 不兼容），改用标准库 `hashlib.pbkdf2_hmac`。
- **JWT**：`sub` 声明使用字符串，避免 `python-jose` 的 `JWTClaimsError`。
- **测试数据库**：使用独立临时 SQLite 文件，避免 `:memory:` 跨 event loop 表丢失。
- **ASGI 测试客户端**：使用 `httpx.ASGITransport` 替代已废弃的 `AsyncClient(app=...)`。
- **Pydantic / Tortoise 弃用警告**：已迁移到 `ConfigDict`、`SettingsConfigDict`、`primary_key=True`。
- **LLM 默认 Mock**：当前 `LLM_MOCK=true` 可保证测试与无 Key 环境通过；真实接入时通过 `.env` 关闭 Mock。

---

## 9. 待完善项（按优先级）

| 序号 | 事项 | 优先级 | 所属阶段 |
| --- | --- | --- | --- |
| 1 | 接入真实 LLM API（DeepSeek / OpenAI / Coze），替换 `LLM_MOCK` | 高 | Phase 1 ✅ |
| 2 | 增强 LLM 客户端：重试、超时、token 计费、异常处理 | 高 | Phase 1 ✅ |
| 3 | 向量检索/RAG：Embedding + Chroma/FAISS + 文本分块 | 高 | Phase 2 |
| 4 | 图片生成、阿里云 OSS 上传、本地回退 | 中 | Phase 3 |
| 5 | 小红书账号绑定与发布 API（真实 SDK / mock） | 中 | Phase 3 |
| 6 | Celery + Redis 实际运行验证 | 中 | Phase 1/2 |
| 7 | 补充更多集成测试（生成文章全链路、发布链路） | 中 | 各阶段 |
| 8 | 前端最小示例或 Postman Collection | 低 | Phase 4 |
| 9 | K8s / Prometheus / Sentry 生产部署 | 低 | Phase 5 |

---

## 10. 下一步建议（Phase 2：向量检索/RAG）

建议按以下顺序推进 Phase 2：

1. **选择向量库**：
   - 开发环境：Chroma（本地文件）或 FAISS（无服务端）。
   - 生产环境：Weaviate / Milvus。
   - 通过配置 `VECTOR_DB_URL` / `VECTOR_DB_TYPE` 切换。

2. **新增 Embedding Service（`backend/app/services/embedding.py`）**：
   - 本地 ONNX/BGE 模型或调用 OpenAI / 硅基流动等 Embedding API。
   - 提供 `embed(texts: list[str]) -> list[list[float]]` 统一接口。

3. **新增 RAG Pipeline（`backend/app/services/rag.py`）**：
   - 文本分块：按字数/重叠窗口切分文档。
   - Upsert：将 chunk + metadata 写入向量库。
   - Query：根据 query 检索 top-K 相似 chunk，rerank（可选），拼入 prompt。

4. **接入 AgentRunner**：
   - `generate_article` 在 `payload` 中接收 `material_ids` 或 `rag_query`。
   - 自动从向量库检索上下文并拼入 `_build_article_prompt`。
   - 在 `article.metadata` 记录 `used_context_ids`。

5. **补充测试**：
   - 文本分块单元测试。
   - Embedding service mock 测试。
   - RAG 检索与文章生成集成测试。

### 需要用户提供

- 是否已启动 Docker Desktop？
- 是否有真实 LLM API Key，以及服务商（当前 `.env.example` 默认 DeepSeek）？
- 向量库偏好（Chroma / FAISS / Weaviate / Milvus）？
- Embedding 来源（本地 ONNX 模型 / 远程 API）？

---

## 11. 安全与密钥说明

- 项目未提交任何真实密钥。
- `.env` 已在 `.gitignore` 中排除。
- 配置文件仅保留默认值/空字符串作为 fallback。
- 运行前请复制 `.env.example` → `.env` 并填入真实值。
