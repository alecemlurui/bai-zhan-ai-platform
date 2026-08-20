# 百战智能运营平台 — 开发进度报告

> 报告时间：2026-08-20
> 项目路径：`D:/ai agent学习/rag/bai-zhan-ai-platform/`
> GitHub：`https://github.com/alecemlurui/bai-zhan-ai-platform`
> 本报告不含任何 API Key / JWT Secret / 数据库凭证。

---

## 1. 项目概况

基于 FastAPI + Tortoise ORM + Aerich + Celery + Docker 的后端服务，已按 14 步开发/验收规范完成 **Phase 0–5**，并额外补充了：

- 项目骨架、一键脚本、QA 基线
- 用户认证、基础 API
- 真实 LLM 接入（重试、计费、异常）
- 向量检索 / RAG（ONNX Embedding + Chroma）
- 图片生成与 OSS/本地上传
- 小红书 / 第三方发布流程
- CI/CD、监控、K8s 生产部署清单
- **前端示例（原生 JS SPA）**
- **DeepSeek 付费 API 真实联调验证**

当前代码已推送 GitHub，`pytest 44 passed`，代码覆盖率 75%，`black/isort/flake8/mypy/bandit` 全绿。Docker 容器组已成功启动并跑通端到端冒烟测试。

---

## 2. 当前完成度（按里程碑）

| 里程碑 | 状态 | 说明 |
| --- | --- | --- |
| A. 项目骨架与环境 | ✅ 完成 | Dockerfile、docker-compose、requirements、README、一键脚本 |
| B. 数据库与 ORM | ✅ 完成 | Tortoise 模型、`aerich` 迁移（init + platform_account） |
| C. 用户认证 | ✅ 完成 | 注册/登录/JWT/依赖注入，测试通过 |
| D. 基础 API | ✅ 完成 | Health、Topics、Titles、Articles、Publish、RAG、Accounts |
| E. Agent / 任务流 | ✅ 完成 | `AgentRunner` + Celery worker + `Task` 状态机 |
| F. 媒体与素材 | ✅ 完成 | 图片生成（Mock/Remote/SD）、OSS/本地上传 |
| G. 向量检索/RAG | ✅ 完成 | ONNX Embedding + Chroma + 文本分块 + Agent 自动检索 |
| H. 前端示例 | ✅ 完成 | 已新增 `frontend/` 原生 JS SPA，支持登录/主题/标题/文章/封面/发布/RAG/任务轮询；Docker 挂载并已验证访问 `http://localhost:8000/` |
| I. 部署/监控 | ✅ 完成 | CI、K8s manifests、Sentry + Prometheus 接入点 |
| J. 代码质量与 CI | ✅ 完成 | black/isort/flake8/mypy/bandit、CI workflow |
| K. 真实 LLM 接入 | ✅ 完成 | LLMClient 增强：重试、超时、计费、异常分类 |
| L. 图片/OSS | ✅ 完成 | `/media/generate`、`/articles/generate-cover` |
| M. 小红书/第三方发布 | ✅ 完成 | PlatformAccount、Mock/Sandbox Publisher |

---

## 3. 提交历史

| 阶段 | Commit |
| --- | --- |
| Phase 0 | `9cb4046 feat(dev): Phase 0 dev baseline and one-click scripts` |
| Phase 1 | `525a85f feat(llm): Phase 1 real LLM integration with retry, cost and structured errors` |
| Phase 2 | `1013c55 feat(rag): Phase 2 vector retrieval with ONNX embedding + Chroma store` |
| Phase 3 | `ca1488e feat(media): Phase 3 image generation and OSS/local upload` |
| Phase 4 | `12221db feat(publish): Phase 4 XiaoHongShu/third-party publish flow with accounts` |
| Phase 5 | `34c3be3 feat(ops): Phase 5 CI/CD, monitoring and production deployment checklist` |

---

## 4. 真实 LLM 联调结果（DeepSeek）

配置（本地 `.env`，未提交 Git）：

```bash
LLM_API_KEY=sk-********************************
LLM_BASE_URL=https://api.deepseek.com/v1
LLM_MODEL=deepseek-chat
LLM_MOCK=false
```

执行端到端冒烟测试：

```bash
python scripts/e2e_smoke.py
```

结果：

```text
[1/6] register user: smoke_b567d5af
  -> registered
[2/6] login
  -> got token
[3/6] create topic
  -> topic_id=2
[4/6] generate titles
  -> title task_id=3, status=pending
  -> title task final: success
  -> generated 5 titles
     - DeepSeek vs 传统LLM：联调对比评测...
     - 我用DeepSeek做了次LLM联调，结果…...
     - DeepSeek联调测试：这3个坑你绝对想不到...
[5/6] generate article from title_id=8
  -> article task_id=4, status=pending
  -> article task final: success
  -> task.result: {'model': 'deepseek-v4-flash', 'tokens': 389, 'cost_usd': 0.0, 'title_id': 8, 'article_id': 2, 'latency_ms': 3450.43, 'used_context_ids': []}
[6/6] article length=440
PASS
```

关键结论：

- 标题生成与文章生成均调用 DeepSeek 真实接口，返回内容不再是 `【模拟 LLM 回答】`。
- `task.result` 中 `model`、`tokens`、`latency_ms` 已记录真实值（API 返回模型为 `deepseek-v4-flash`）。
- `cost_usd` 为 0 是因为 `.env` 中 `LLM_INPUT_PRICE_PER_1M` / `LLM_OUTPUT_PRICE_PER_1M` 保持 0；填入 DeepSeek 官方单价后即可自动估算费用。

---

## 5. 验证结果

本地 CI 检查链（项目根执行）：

```bash
set LLM_MOCK=true
set JWT_SECRET=test-secret
backend/.venv/Scripts/python.exe -m black --check backend
backend/.venv/Scripts/python.exe -m isort --check-only backend
backend/.venv/Scripts/python.exe -m flake8 backend
cd backend && .venv/Scripts/python.exe -m mypy . --ignore-missing-imports
backend/.venv/Scripts/python.exe -m bandit -r backend/app backend/tests -ll
backend/.venv/Scripts/python.exe -m pytest -q --cov=backend/app
```

结果：

```text
black: 40 files would be left unchanged
isort: Skipped 2 files
flake8: 无错误
mypy: Success: no issues found in 38 source files
bandit: No issues identified. Medium: 0, High: 0
pytest: 44 passed, 覆盖率 75%
```

---

## 6. 关键文件结构

```text
bai-zhan-ai-platform/
├── .env.example
├── .flake8
├── .gitignore
├── docker-compose.yml
├── pytest.ini
├── README.md
├── .github/
│   └── workflows/
│       └── ci.yml
├── infra/
│   └── k8s/
│       ├── namespace.yaml
│       ├── configmap.yaml
│       ├── secret.yaml
│       ├── web-deployment.yaml
│       ├── worker-deployment.yaml
│       ├── service.yaml
│       └── ingress.yaml
├── scripts/
│   ├── dev_up.sh / dev_up.ps1
│   ├── ci_check.sh / ci_check.ps1
│   ├── deploy_k8s.sh
│   ├── e2e_test.sh
│   └── e2e_smoke.py
├── frontend/
│   ├── index.html
│   └── static/
│       ├── app.js
│       └── styles.css
└── backend/
    ├── Dockerfile
    ├── requirements.txt
    ├── pyproject.toml
    ├── app/
    │   ├── main.py              # FastAPI + Sentry + Prometheus /metrics + 前端挂载
    │   ├── config.py
    │   ├── models.py
    │   ├── schemas.py
    │   ├── dependencies.py
    │   ├── router.py
    │   ├── api/
    │   │   ├── accounts.py
    │   │   ├── articles.py
    │   │   ├── auth.py
    │   │   ├── health.py
    │   │   ├── materials.py
    │   │   ├── media.py
    │   │   ├── publish.py
    │   │   ├── rag.py
    │   │   ├── tasks.py
    │   │   ├── titles.py
    │   │   └── topics.py
    │   ├── services/
    │   │   ├── agent_runner.py
    │   │   ├── auth.py
    │   │   ├── auth_service.py
    │   │   ├── embedding.py
    │   │   ├── image_generator.py
    │   │   ├── llm_client.py
    │   │   ├── media.py
    │   │   ├── oss_uploader.py
    │   │   ├── publisher.py
    │   │   ├── rag.py
    │   │   ├── topic.py
    │   │   └── vector_store.py
    │   ├── tasks.py
    │   └── worker.py
    ├── migrations/
    │   └── models/
    │       └── 0_20260820080634_init.py
    └── tests/
        ├── conftest.py
        ├── test_agent.py
        ├── test_auth.py
        ├── test_llm_integration.py
        ├── test_media.py
        ├── test_publish.py
        ├── test_rag.py
        └── test_topics.py
```

---

## 7. 主要 API 清单

| 方法 | 路径 | 说明 |
| --- | --- | --- |
| POST | /api/v1/auth/register | 用户注册 |
| POST | /api/v1/auth/login | 用户登录 |
| GET | /api/v1/health | 健康检查 |
| POST | /api/v1/topics | 创建主题 |
| POST | /api/v1/topics/{id}/generate-titles | 生成标题（Celery 任务） |
| POST | /api/v1/articles/generate | 生成文章（支持 RAG） |
| POST | /api/v1/articles/generate-cover | 生成封面图 |
| POST | /api/v1/media/upload | 上传媒体 |
| POST | /api/v1/media/generate | 生成图片 |
| POST | /api/v1/rag/ingest/{material_id} | 素材向量化入库 |
| GET | /api/v1/rag/search | 向量检索 |
| POST | /api/v1/accounts | 绑定平台账号 |
| POST | /api/v1/publish | 发布到第三方平台 |
| GET | /api/v1/publish/article/{article_id} | 查询发布记录 |
| GET | /api/v1/tasks/{task_id} | 任务状态查询 |
| GET | / | 前端单页应用 |
| GET | /metrics | Prometheus 指标 |

---

## 8. 主要技术决策

- **密码哈希**：`hashlib.pbkdf2_hmac`（避免 passlib/bcrypt 版本冲突）。
- **JWT**：`sub` 使用字符串，兼容 `python-jose`。
- **测试数据库**：独立临时 SQLite 文件，避免 `:memory:` 跨 event loop 丢失。
- **ASGI 测试**：`httpx.ASGITransport`。
- **LLM / Embedding / 图片生成 / 上传 / 发布**：默认 Mock 模式，保证无 Key 环境可测试；真实环境通过 `.env` 切换。
- **RAG**：本地 ONNX BGE + Chroma；抽象接口可切换远程 Embedding / Weaviate。
- **Celery**：Redis 作为 broker/result backend；worker 在 docker-compose 中独立启动。
- **监控**：Sentry 错误追踪 + Prometheus `/metrics` 端点。
- **前端**：原生 JS SPA，位于 `frontend/`，由后端 `/` 与 `/static` 挂载，零构建工具。
- **部署**：Docker + docker-compose 本地；K8s manifests 用于 staging/prod。
- **数据库**：Tortoise ORM >=1.0 在 lifespan 中需开启 `_enable_global_fallback=True`，避免 FastAPI 请求 task 丢失上下文。

---

## 9. 已知阻塞与环境问题

| 问题 | 状态 | 说明 |
| --- | --- | --- |
| Docker Desktop 已运行 | ✅ 已确认 | `docker info` 返回版本 29.1.5；`docker-compose up -d` 成功启动 web/worker/postgres/redis。 |
| DeepSeek API Key | ✅ 已提供 | 已写入本地 `.env`（已加入 `.gitignore`，未进入 Git），`LLM_MOCK=false` 并已真实联调通过。 |
| 前端界面 | ✅ 完成 | `frontend/` 已创建并挂载，访问 `http://localhost:8000/` 可正常加载 SPA。 |
| Postgres 迁移 | ✅ 已修复 | 旧迁移为 SQLite 方言，已重新生成为 Postgres 兼容的 `SERIAL`/`JSONB`/`TIMESTAMPTZ` 版本。 |
| Tortoise ORM 1.x 上下文 | ✅ 已修复 | `main.py` lifespan 增加 `_enable_global_fallback=True`，避免请求 task 丢失 DB 上下文。 |
| LLM Base URL 双写 /v1 | ✅ 已修复 | `llm_client.py` 现在兼容 base_url 带或不带 `/v1` 两种配置习惯。 |

---

## 10. 下一步建议（进入真实联调与上线准备）

1. **完成剩余真实服务联调**：
   - 配置本地 ONNX 模型路径（`EMBEDDING_MODEL_PATH`），关闭 `EMBEDDING_MOCK`，验证 RAG 检索增强文章生成。
   - 配置阿里云 OSS，切换 `UPLOADER_MODE=oss`，验证图片上传与可访问 URL。
   - 配置小红书/第三方平台账号与 API，关闭 `XIAOHONGSHU_MOCK`，验证真实发布流程。

2. **Docker 端到端验证**：
   - 保持 `docker-compose up -d` 运行。
   - 运行 `python scripts/e2e_smoke.py` 复验标题/文章真实 LLM 链路。

3. **性能与安全加固**：
   - 平台账号 credentials 加密存储。
   - 图片/发布任务限流、重试策略细化。
   - 生产环境 secret 管理（K8s Secret / Vault）。
   - 前端接入真实 OSS 图片预览与发布结果回显。

---

## 11. 安全与密钥说明

- 项目未提交任何真实密钥。
- `.env` 已在 `.gitignore` 中排除。
- `infra/k8s/secret.yaml` 使用占位符，生产前必须替换并通过密封 Secret / Vault 注入。
- 运行前请复制 `.env.example` → `.env` 并填入真实值。
