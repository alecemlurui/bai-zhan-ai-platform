# 百战智能运营平台 — 开发进度报告

> 报告时间：2026-08-20
> 项目路径：`D:/ai agent学习/rag/bai-zhan-ai-platform/`
> GitHub：`https://github.com/alecemlurui/bai-zhan-ai-platform`
> 本报告不含任何 API Key / JWT Secret / 数据库凭证。

---

## 1. 项目概况

基于 FastAPI + Tortoise ORM + Aerich + Celery + Docker 的后端骨架，覆盖用户认证、主题/题目/文章生成、任务工作流、媒体/OSS、小红书发布、素材库、向量检索/RAG 等核心模块。当前已完成 **Phase 0/1/2**（开发基线、LLM 接入、RAG），代码已推送 GitHub，CI 全绿。

---

## 2. 当前完成度（按里程碑）

| 里程碑 | 状态 | 说明 |
| --- | --- | --- |
| A. 项目骨架与环境 | ✅ 完成 | Dockerfile、docker-compose、requirements、README、一键脚本已到位 |
| B. 数据库与 ORM | ✅ 完成 | Tortoise 模型、`aerich` 迁移、初始 schema 已提交 |
| C. 用户认证 | ✅ 完成 | 注册/登录/JWT/依赖注入，测试通过 |
| D. 基础 API | ✅ 完成 | Health、Topics、Titles、Articles、Publish、RAG 路由 |
| E. Agent / 任务流 | ✅ 完成 | `AgentRunner` + Celery worker + `Task` 状态机，可触发任务 |
| F. 媒体与素材 | ✅ Phase 3 完成 | 图片生成（Mock/Remote/SD）+ OSS/本地上传 + Media 表记录 |
| G. 向量检索/RAG | ✅ Phase 2 完成 | ONNX Embedding + Chroma 向量库 + 文本分块 + Agent 自动检索 |
| H. 前端示例 | ⏳ 未开始 | 仅提供 OpenAPI/Postman |
| I. 部署/监控 | ⏳ 未开始 | Docker 已提供，K8s/监控待补 |
| J. 代码质量与 CI | ✅ 基线完成 | black/isort/flake8/mypy/bandit 配置通过；ci_check 脚本可用 |
| K. 真实 LLM 接入 | ✅ Phase 1 完成 | LLMClient 增强：重试、超时、计费、异常分类；Agent prompt 结构化 |
| L. 图片/OSS | ✅ Phase 3 完成 | /media/generate、/articles/generate-cover、LocalUploader/OssUploader |

---

## 3. Phase 0：开发基线（已完成）

- 一键脚本：`scripts/dev_up.sh/ps1`、`scripts/ci_check.sh/ps1`
- QA 工具配置：`black` / `isort` / `flake8` / `mypy` / `bandit` / `pre-commit`
- 代码风格与类型修复
- 提交：`9cb4046`

---

## 4. Phase 1：真实 LLM 接入（已完成）

- LLMClient：指数退避重试、超时处理、token/费用估算、结构化异常（`LLMRateLimitError`、`LLMTimeoutError`、`LLMContentFilterError`、`LLMUnknownError`）
- AgentRunner：结构化 JSON title prompts + fallback 解析，article prompt 支持风格/字数/RAG 上下文
- 新增 `backend/tests/test_llm_integration.py`，覆盖 mock、重试、异常、Agent 全链路
- 提交：`525a85f`

---

## 5. Phase 2：向量检索 / RAG（已完成）

### 5.1 新增服务

- `services/embedding.py`：`OnnxBgeEmbedder` 本地 ONNX 推理 + `MockEmbedder` 测试回退
- `services/vector_store.py`：`ChromaVectorStore` + `MockVectorStore` 抽象
- `services/rag.py`：文本分块、`ingest_material`、`retrieve_context`、`build_rag_prompt_context`

### 5.2 集成与 API

- `AgentRunner._generate_article` 在 `payload.use_rag=true` 时自动检索上下文，记录 `used_context_ids`
- 新增 `api/rag.py`：`/api/v1/rag/ingest`、`/search`、`/context`
- `api/materials.py`：创建文本素材时自动向量化入库，删除时同步清理

### 5.3 配置扩展

- `VECTOR_DB_TYPE` / `VECTOR_DB_PATH` / `VECTOR_DB_URL` / `VECTOR_DB_API_KEY`
- `EMBEDDING_MODEL_PATH` / `EMBEDDING_TOKENIZER_PATH` / `EMBEDDING_MOCK` / `EMBEDDING_VECTOR_SIZE`
- `RAG_CHUNK_SIZE` / `RAG_CHUNK_OVERLAP` / `RAG_TOP_K`

### 5.4 验证结果

```text
black: 34 files would be left unchanged
isort: Skipped 2 files
flake8: 无错误
mypy: Success: no issues found in 33 source files
bandit: No issues identified. Medium: 0, High: 0
pytest: 29 passed in ~22s
```

### 5.5 提交

- `1013c55 feat(rag): Phase 2 vector retrieval with ONNX embedding + Chroma store`

---

## 6. Phase 3：图片生成与 OSS/本地存储（已完成）

### 6.1 新增服务

- `services/image_generator.py`：`BaseImageGenerator` 抽象 + `MockImageGenerator`（PIL）+ `RemoteImageGenerator` + `LocalSdImageGenerator`
- `services/oss_uploader.py`：`BaseUploader` 抽象 + `LocalUploader` 回退 + `OssUploader`（阿里云 OSS）
- `services/media.py`：`generate_image()` 整合生成、上传、元数据提取

### 6.2 API 扩展

- `POST /api/v1/media/generate`：根据 prompt 生成图片并入库
- `POST /api/v1/articles/generate-cover`：为文章生成封面图

### 6.3 配置扩展

- `IMAGE_GENERATOR_MODE` / `IMAGE_API_URL` / `IMAGE_API_KEY` / `IMAGE_MODEL` / `IMAGE_TIMEOUT`
- `UPLOADER_MODE`（local | oss）

### 6.4 验证结果

```text
black: 37 files would be left unchanged
isort: Skipped 2 files
flake8: 无错误
mypy: Success: no issues found in 36 source files
bandit: No issues identified. Medium: 0, High: 0
pytest: 36 passed in ~23s
```

### 6.5 提交

- `ca1488e feat(media): Phase 3 image generation and OSS/local upload`

---

## 7. 已知阻塞与环境问题

| 问题 | 状态 | 说明 |
| --- | --- | --- |
| Docker Desktop 未运行 | ⚠️ 阻塞 | `docker-compose up -d postgres redis` 需要用户启动 Docker Desktop。不影响代码提交与单元测试。 |
| 真实 LLM / OSS / 小红书 API Key 未提供 | ⚠️ 配置缺失 | 当前使用 Mock 模式保证测试通过；真实联调需用户补充 `.env`。 |
| ONNX 模型路径未配置 | ⚠️ 配置缺失 | 已默认 `EMBEDDING_MOCK=true`；真实推理需配置 `EMBEDDING_MODEL_PATH`。 |

---

## 8. 代码提交与远程同步

- Phase 0：`9cb4046 feat(dev): Phase 0 dev baseline and one-click scripts`
- Phase 1：`525a85f feat(llm): Phase 1 real LLM integration with retry, cost and structured errors`
- Phase 2：`1013c55 feat(rag): Phase 2 vector retrieval with ONNX embedding + Chroma store`
- Phase 3：`ca1488e feat(media): Phase 3 image generation and OSS/local upload`
- 已推送至：`git@github.com:alecemlurui/bai-zhan-ai-platform.git` 的 `main` 分支
- 未提交任何真实密钥；`.env` 已受 `.gitignore` 保护。

---

## 9. 关键文件结构

```text
bai-zhan-ai-platform/
├── .env.example
├── .flake8
├── .gitignore
├── docker-compose.yml
├── pytest.ini
├── README.md
├── .github/workflows/ci.yml
├── scripts/
│   ├── dev_up.sh / dev_up.ps1
│   ├── ci_check.sh / ci_check.ps1
├── backend/
│   ├── Dockerfile
│   ├── requirements.txt
│   ├── pyproject.toml
│   ├── app/
│   │   ├── main.py
│   │   ├── config.py
│   │   ├── models.py
│   │   ├── schemas.py
│   │   ├── dependencies.py
│   │   ├── router.py
│   │   ├── api/
│   │   │   ├── articles.py
│   │   │   ├── auth.py
│   │   │   ├── health.py
│   │   │   ├── materials.py
│   │   │   ├── media.py
│   │   │   ├── publish.py
│   │   │   ├── rag.py
│   │   │   ├── titles.py
│   │   │   └── topics.py
│   │   ├── services/
│   │   │   ├── agent_runner.py
│   │   │   ├── auth_service.py
│   │   │   ├── embedding.py
│   │   │   ├── image_generator.py
│   │   │   ├── llm_client.py
│   │   │   ├── media.py
│   │   │   ├── oss_uploader.py
│   │   │   ├── publisher.py
│   │   │   ├── rag.py
│   │   │   ├── topic.py
│   │   │   └── vector_store.py
│   │   ├── tasks.py
│   │   └── worker.py
│   ├── migrations/models/
│   └── tests/
│       ├── conftest.py
│       ├── test_agent.py
│       ├── test_auth.py
│       ├── test_llm_integration.py
│       ├── test_media.py
│       ├── test_rag.py
│       └── test_topics.py
└── docs/
    └── PROGRESS.md
```

---

## 10. 主要技术决策

- **密码哈希**：弃用 `passlib+bcrypt`，改用 `hashlib.pbkdf2_hmac`。
- **JWT**：`sub` 声明使用字符串，避免 `python-jose` 的 `JWTClaimsError`。
- **测试数据库**：使用独立临时 SQLite 文件，避免 `:memory:` 跨 event loop 表丢失。
- **ASGI 测试客户端**：`httpx.ASGITransport`。
- **Pydantic / Tortoise**：迁移到 `ConfigDict`、`SettingsConfigDict`、`primary_key=True`。
- **LLM / Embedding / Vector Store Mock**：默认 Mock 模式，保证无 Key 环境可测试。
- **RAG**：本地 ONNX BGE + Chroma；抽象接口便于切换远程 Embedding / Weaviate。
- **图片生成 / 上传**：默认 Mock 生成器（PIL）与本地上传器，预留 Remote/SD/OSS 接入。

---

## 11. 待完善项（按优先级）

| 序号 | 事项 | 优先级 | 所属阶段 |
| --- | --- | --- | --- |
| 1 | 图片生成（调用 SD / DALL-E / 即梦等） | 高 | Phase 3 |
| 2 | 阿里云 OSS 上传与本地回退 | 高 | Phase 3 |
| 3 | 小红书账号绑定与发布 API | 高 | Phase 4 |
| 4 | 真实 LLM / Embedding / OSS Key 联调 | 高 | Phase 5 |
| 5 | Celery + Redis 实际运行验证 | 中 | Phase 5 |
| 6 | GitHub Actions CI workflow 补全 | 中 | Phase 5 |
| 7 | 前端最小示例或 Postman Collection | 低 | Phase 6 |
| 8 | K8s / Prometheus / Sentry 生产部署 | 低 | Phase 7 |

---

## 12. 下一步建议（Phase 4：小红书发布流程）

建议按以下顺序推进 Phase 4：

1. **账号管理模型**：
   - 新增 `PlatformAccount` 表：platform、account_name、credentials（JSON 加密或安全存储）、is_active。

2. **发布服务增强（`services/publisher.py`）**：
   - 保留 `XiaoHongShuPublisher` mock 实现。
   - 新增 `SandboxPublisher` 与真实 HTTP publisher 适配层。
   - 支持选择账号、重试、失败记录。

3. **API 路由**：
   - `POST /api/v1/publish`：指定 article_id + account_id，创建发布任务。
   - `GET /api/v1/publish_records`：查询发布历史。
   - `POST /api/v1/accounts`：绑定第三方账号。

4. **AgentRunner 集成**：
   - 将 publish 任务类型接入 Celery worker，调用 publisher 并回填 `PublishRecord`。

5. **测试**：
   - Mock 发布成功/失败场景。
   - 验证发布历史记录与状态流转。

### 需要用户提供

- 是否已启动 Docker Desktop？
- 小红书/第三方平台开发者账号与 API 文档（可选，未配置则使用 mock）。
- 是否需要账号凭证加密存储？（当前阶段可先用 JSON 明文，生产前升级。）

---

## 13. 安全与密钥说明

- 项目未提交任何真实密钥。
- `.env` 已在 `.gitignore` 中排除。
- 配置文件仅保留默认值/空字符串作为 fallback。
- 运行前请复制 `.env.example` → `.env` 并填入真实值。
