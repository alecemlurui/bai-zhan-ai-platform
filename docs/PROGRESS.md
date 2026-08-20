# 百战智能运营平台 — 开发进度报告

> 报告时间：2026-08-20
> 项目路径：`D:/ai agent学习/rag/bai-zhan-ai-platform/`
> GitHub：`https://github.com/alecemlurui/bai-zhan-ai-platform`
> 本报告不含任何 API Key / JWT Secret / 数据库凭证。

---

## 1. 项目概况

基于 FastAPI + Tortoise ORM + Aerich + Celery + Docker 的后端服务，已按 14 步开发/验收规范完成 **Phase 0–5**：

- 项目骨架、一键脚本、QA 基线
- 用户认证、基础 API
- 真实 LLM 接入（重试、计费、异常）
- 向量检索 / RAG（ONNX Embedding + Chroma）
- 图片生成与 OSS/本地上传
- 小红书 / 第三方发布流程
- CI/CD、监控、K8s 生产部署清单

当前代码已推送 GitHub，`pytest 44 passed`，代码覆盖率 75%，`black/isort/flake8/mypy/bandit` 全绿。

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
| H. 前端示例 | ⏳ 未开始 | 提供 OpenAPI/Postman + e2e 脚本 |
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

## 4. 验证结果

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

## 5. 关键文件结构

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
│   └── e2e_test.sh
└── backend/
    ├── Dockerfile
    ├── requirements.txt
    ├── pyproject.toml
    ├── app/
    │   ├── main.py              # FastAPI + Sentry + Prometheus /metrics
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
    │   │   ├── titles.py
    │   │   └── topics.py
    │   ├── services/
    │   │   ├── agent_runner.py
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
    │       ├── 0_20260819152127_init.py
    │       └── 1_20260820121909_add_platform_account.py
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

## 6. 主要 API 清单

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
| GET | /metrics | Prometheus 指标 |

---

## 7. 主要技术决策

- **密码哈希**：`hashlib.pbkdf2_hmac`（避免 passlib/bcrypt 版本冲突）。
- **JWT**：`sub` 使用字符串，兼容 `python-jose`。
- **测试数据库**：独立临时 SQLite 文件，避免 `:memory:` 跨 event loop 丢失。
- **ASGI 测试**：`httpx.ASGITransport`。
- **LLM / Embedding / 图片生成 / 上传 / 发布**：默认 Mock 模式，保证无 Key 环境可测试；真实环境通过 `.env` 切换。
- **RAG**：本地 ONNX BGE + Chroma；抽象接口可切换远程 Embedding / Weaviate。
- **Celery**：Redis 作为 broker/result backend；worker 在 docker-compose 中独立启动。
- **监控**：Sentry 错误追踪 + Prometheus `/metrics` 端点。
- **部署**：Docker + docker-compose 本地；K8s manifests 用于 staging/prod。

---

## 8. 已知阻塞与环境问题

| 问题 | 状态 | 说明 |
| --- | --- | --- |
| Docker Desktop 未运行 | ⚠️ 阻塞 | 需用户启动 Docker Desktop 后运行 `docker-compose up --build`。不影响单元测试。 |
| 真实 API Key 未提供 | ⚠️ 配置缺失 | LLM / OSS / 小红书等使用 Mock 模式；真实联调需补充 `.env`。 |
| 前端界面 | ⏳ 未开始 | 当前为纯后端 API；最小前端/Postman Collection 待补充。 |

---

## 9. 下一步建议（进入真实联调与上线准备）

1. **真实服务联调**：
   - 配置 DeepSeek / OpenAI LLM API Key，关闭 `LLM_MOCK`。
   - 配置本地 ONNX 模型路径（`EMBEDDING_MODEL_PATH`），关闭 `EMBEDDING_MOCK`。
   - 配置阿里云 OSS，切换 `UPLOADER_MODE=oss`。
   - 配置小红书/第三方平台账号与 API，关闭 `XIAOHONGSHU_MOCK`。

2. **Docker 端到端验证**：
   - 启动 Docker Desktop。
   - 运行 `docker-compose up --build`。
   - 运行 `scripts/e2e_test.sh` 验证全链路。

3. **前端/Postman**：
   - 提供最小前端示例或 Postman Collection，供业务方验收。

4. **性能与安全加固**：
   - 平台账号 credentials 加密存储。
   - 图片/发布任务限流、重试策略细化。
   - 生产环境 secret 管理（K8s Secret / Vault）。

---

## 10. 安全与密钥说明

- 项目未提交任何真实密钥。
- `.env` 已在 `.gitignore` 中排除。
- `infra/k8s/secret.yaml` 使用占位符，生产前必须替换并通过密封 Secret / Vault 注入。
- 运行前请复制 `.env.example` → `.env` 并填入真实值。
