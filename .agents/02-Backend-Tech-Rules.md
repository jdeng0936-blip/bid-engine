# ⚙️ 后端与 AI 技术栈约束

## 基础框架
1. **后端**：FastAPI (Python 3.11+) + Uvicorn，严格使用 `async/await` 异步编程，**禁止**同步阻塞函数
2. **前端**：Next.js 15 + React 19 + TypeScript，App Router 模式，所有组件严格类型定义
3. **AI 对话流**：单向流式输出用 SSE；双向高频刷新用 WebSocket + Redis Pub/Sub
4. **接口规范**：所有 API 必须进行 JWT 鉴权；统一使用 Pydantic V2 进行 Schema 校验
5. **测试框架**：统一使用 pytest 和 pytest-asyncio；路由测试用 `httpx.AsyncClient`；数据库测试通过 `dependency_overrides` 替换回滚 session

## AI 模型调用规范
1. **统一入口**：所有 LLM 调用必须通过 LiteLLM 网关（`OPENAI_BASE_URL` 配置的地址），禁止直连各云厂商 SDK
2. **模型动态路由**：通过 `LLMSelector.get_model(task_type)` 查 `llm_registry.yaml`，禁止硬编码模型名
3. **Prompt 版本管理**：通过 `prompt_manager.get(prompt_name)` 查 `prompts_registry.yaml`，禁止硬编码 Prompt 字符串
4. **Fallback 机制**：`llm_registry.yaml` 每个 task 配多个模型，SDK 自动降级，业务层不做重试逻辑
5. **可观测性**：所有 LLM 调用通过 LangFuse 埋点，高质量输出打 `quality:high` 标签

## 数据层规范
1. **向量数据库**：使用 PostgreSQL 16 + pgvector 扩展，禁止引入独立向量库
2. **多租户隔离**：所有 DB 查询和 pgvector 语义检索，第一步必须注入 `tenant_id` 过滤
3. **RAG 三层架构**：L1语义检索 → L2结构化查表 → L3融合排序，禁止全量数据灌 Prompt
4. **缓存**：会话状态和 WebSocket 状态管理用 Redis，客户端必须实现心跳保活

## 文档生成规范
1. **质量闭环**：所有 AI 生成章节必须经过 Critic 自评打分，≥8分通过，否则重写
2. **一致性扫描**：多章节生成后必须运行跨章节一致性扫描（数值/人员/设备）
3. **计算引擎**：安全关键数值（支护/通风等）必须走计算引擎精确计算，LLM 只解读结果
4. **输出格式**：最终文档输出为 Word（`.docx`），存 `backend/storage/outputs/`，不入库 Git
