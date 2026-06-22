# “诉智达”MVP 实施计划

> **面向执行者：** 如环境支持子智能体，优先使用 `$subagent-driven-development`；否则使用 `$executing-plans`。每个任务都按顺序完成，不得跳跃。

## 1. 计划目标

构建一个可演示、可评估、可本地部署、可逐步走向私有化生产的投诉智能处置 MVP。系统采用“单智能体 + LangGraph 状态机 + 局部循环”架构，围绕投诉理解、混合检索、证据驱动生成、规则校验、人工确认和反馈闭环展开。

## 2. 技术栈与时间线约束

### 2.1 技术栈

- 后端：`Python 3.11`、`FastAPI`、`Pydantic v2`、`SQLAlchemy 2`、`Alembic`、`LangGraph`
- 检索与数据：`Milvus`、`Elasticsearch`、`Redis`、`MySQL 8`
- 模型服务：`vLLM`、`Qwen2.5-14B-Instruct`、`BGE-M3`、`BGE-reranker`
- 前端：`Vue 3`、`TypeScript`、`Vite`、`Pinia`
- 测试：`pytest`、`Vitest`、`Playwright`
- 运维：`Docker Compose`、`Prometheus`

### 2.2 历史兼容性约束

- 简历项目周期固定为 `2025-06` 至 `2026-04`。
- 运行时依赖、容器镜像、模型版本、接口能力与技术表述都必须满足 `2026-04-30` 前已公开可用。
- 当前重建过程允许使用 Superpowers 提升执行质量，但不得把 Superpowers 写入原项目技术栈。
- 如发生版本升级，必须在验收文档中注明升级时间、原因和兼容影响。

### 2.3 锁定版本基线

| 组件 | 建议版本 | 说明 |
|---|---:|---|
| Python | 3.11.x | 项目统一运行时 |
| FastAPI | 0.115.12 | 时间线内可用 |
| Pydantic | 2.11.5 | 时间线内可用 |
| SQLAlchemy | 2.0.41 | 时间线内可用 |
| Alembic | 1.15.2 | 与 SQLAlchemy 2 搭配 |
| LangGraph | 1.0.5 | 视作项目后期升级版本 |
| httpx | 0.28.1 | HTTP 调用统一依赖 |
| PyMilvus | 2.5.10 | 对应 Milvus 2.5.x |
| Elasticsearch client | 8.17.2 | 对应 ES 8.17.x |
| redis-py | 5.2.1 | 对应 Redis 7.2.x |
| Vue | 3.5.13 | 前端主框架 |
| Pinia | 2.3.1 | 状态管理 |
| Vite | 6.1.x | 前端构建 |
| TypeScript | 5.7.x | 类型系统 |
| Vitest | 3.0.x | 前端单元测试 |
| Playwright | 1.50.x | 浏览器测试 |
| vLLM | 0.8.5 | 私有推理网关 |

不要静默替换成更新版本。

## 3. 命令约定

除非任务另有说明，命令都在仓库根目录下用 PowerShell 执行。进入子目录时使用：

```powershell
Push-Location <目录>
try {
  <命令>
} finally {
  Pop-Location
}
```

不要使用只适用于 Bash 的临时环境变量写法。

## 4. 参考文档

- 需求与设计文档：`docs/superpowers/specs/2026-06-15-suzhida-complaint-agent-design.md`
- 当前仓库说明：`README.md`
- 本地协作规范：`AGENTS.md`

## 5. 目标目录结构

```text
.
├── AGENTS.md
├── README.md
├── .env.example
├── docker-compose.yml
├── backend/
├── frontend/
├── data/
├── docs/
├── infra/
└── scripts/
```

---

## 分块一：基础能力与持久化

### 任务 1：初始化仓库与质量门禁

**涉及文件：**

- 创建 `.gitignore`、`.env.example`、`docker-compose.yml`、`Makefile`
- 创建 `backend/pyproject.toml`、`backend/app/__init__.py`
- 创建 `backend/tests/conftest.py`、`backend/tests/unit/test_project_layout.py`
- 创建 `frontend/package.json`
- 修改 `README.md`

**执行步骤：**

- [ ] 确认本机安装 `Python 3.11` 与 `Node.js 20+`
- [ ] 建立后端最小依赖清单与前端锁定版本依赖
- [ ] 创建 `.venv` 并安装 `backend[dev]`
- [ ] 先写仓库结构冒烟测试，并确认其先失败
- [ ] 补齐后端开发配置、根目录命令、环境示例和初始说明
- [ ] 完成最小测试夹具并重新运行冒烟测试直至通过
- [ ] 运行一次全量基础检查并提交

**提交信息：**

```bash
git commit -m "chore: bootstrap suzhida workspace"
```

### 任务 2：配置、日志与健康检查接口

**涉及文件：**

- 创建 `backend/app/core/config.py`
- 创建 `backend/app/core/logging.py`
- 创建 `backend/app/core/tracing.py`
- 创建 `backend/app/api/errors.py`
- 创建 `backend/app/main.py`
- 创建 `backend/tests/unit/core/test_config.py`
- 创建 `backend/tests/unit/core/test_logging.py`
- 创建 `backend/tests/integration/api/test_health.py`
- 创建 `backend/tests/integration/api/test_tracing.py`

**执行步骤：**

- [ ] 先写失败的配置测试，验证 API 前缀和日志安全边界
- [ ] 实现类型化 `Settings`，包含数据库、检索、模型与超时配置
- [ ] 增加生产环境校验：私有模型地址不能为空，且不能指向假网关
- [ ] 先写健康检查测试，再实现 `create_app()` 与 `/health`
- [ ] 实现请求追踪 ID 中间件和统一错误响应结构
- [ ] 先写日志安全测试，再实现脱敏日志处理器
- [ ] 复跑配置、日志、健康和追踪测试并提交

**提交信息：**

```bash
git commit -m "feat: add service configuration and health API"
```

### 任务 3：领域模型与持久化

**涉及文件：**

- 创建 `backend/app/domain/enums.py`、`schemas.py`、`errors.py`
- 创建 `backend/app/db/base.py`、`session.py`
- 创建 `backend/app/db/models/complaint.py`
- 创建 `backend/app/db/models/knowledge.py`
- 创建 `backend/app/db/models/workflow.py`
- 创建 `backend/alembic.ini`、`backend/alembic/env.py`
- 创建 `backend/alembic/versions/0001_initial_schema.py`
- 创建 `backend/tests/unit/domain/test_schemas.py`
- 创建 `backend/tests/integration/db/test_models.py`

**执行步骤：**

- [ ] 先写失败的领域约束测试，例如驳回必须带原因、编辑必须带修改内容
- [ ] 实现枚举、Pydantic Schema 与领域错误
- [ ] 先写失败的持久化测试，验证会话、证据、方案、反馈关联与级联删除
- [ ] 实现 SQLAlchemy 模型与初始迁移
- [ ] 建立 `User`、`ComplaintSession`、`RetrievedEvidence`、`GeneratedSolution`、`HumanFeedback`、`KnowledgeDocument`
- [ ] 跑通领域与数据库集成测试并提交

**提交信息：**

```bash
git commit -m "feat: add complaint domain persistence"
```

### 任务 4：知识脱敏、分块与入库流水线

**涉及文件：**

- 创建 `backend/app/knowledge/masking.py`
- 创建 `backend/app/knowledge/chunking.py`
- 创建 `backend/app/knowledge/ingestion.py`
- 创建 `backend/tests/unit/knowledge/test_masking.py`
- 创建 `backend/tests/unit/knowledge/test_chunking.py`
- 创建 `backend/tests/integration/knowledge/test_ingestion.py`
- 创建 `backend/scripts/ingest_knowledge.py`
- 创建 `data/samples/complaints.jsonl`
- 创建 `data/samples/rules.md`

**执行步骤：**

- [ ] 先写脱敏测试，覆盖手机号、身份证、地址、邮箱等敏感字段
- [ ] 实现规则文档分块、历史工单结构化和元数据生成
- [ ] 先写入库流水线失败测试，再实现导入批次、状态记录与失败原因
- [ ] 准备最小样例知识数据
- [ ] 实现命令行入库脚本
- [ ] 跑通常规单元测试和入库集成测试并提交

**提交信息：**

```bash
git commit -m "feat: add knowledge ingestion pipeline"
```

### 任务 5：外部服务网关与可替换适配器

**涉及文件：**

- 创建 `backend/app/gateways/llm.py`
- 创建 `backend/app/gateways/embeddings.py`
- 创建 `backend/app/gateways/reranker.py`
- 创建 `backend/app/gateways/_base.py`
- 创建 `backend/tests/unit/gateways/test_llm.py`
- 创建 `backend/tests/unit/gateways/test_embeddings.py`
- 创建 `backend/tests/unit/gateways/test_reranker.py`

**执行步骤：**

- [ ] 先写失败测试，定义统一调用契约、超时、重试和错误映射
- [ ] 实现抽象网关基类与真实 HTTP 网关
- [ ] 为单元测试提供确定性假实现
- [ ] 严禁业务代码直接依赖第三方 SDK 细节
- [ ] 跑通网关层测试并提交

**提交信息：**

```bash
git commit -m "feat: add model gateway adapters"
```

### 任务 6：混合检索与证据融合

**涉及文件：**

- 创建 `backend/app/retrieval/contracts.py`
- 创建 `backend/app/retrieval/milvus_store.py`
- 创建 `backend/app/retrieval/elastic_store.py`
- 创建 `backend/app/retrieval/template_store.py`
- 创建 `backend/app/retrieval/hybrid.py`
- 创建 `backend/tests/unit/retrieval/test_hybrid.py`
- 创建 `backend/tests/unit/retrieval/test_template_store.py`
- 创建 `backend/tests/contract/test_milvus_contract.py`
- 创建 `backend/tests/contract/test_elastic_contract.py`

**执行步骤：**

- [ ] 先写失败测试，验证多路召回、去重、归一化和融合排序
- [ ] 定义 `Milvus`、`Elasticsearch`、`Redis` 模板检索契约
- [ ] 实现混合检索器与降级策略
- [ ] 加入证据标识、来源类型、得分和元数据
- [ ] 跑通常规与契约测试并提交

**提交信息：**

```bash
git commit -m "feat: implement hybrid retrieval service"
```

### 任务 7：工作流状态与 Prompt 约束

**涉及文件：**

- 创建 `backend/app/workflow/state.py`
- 创建 `backend/app/workflow/prompts.py`
- 创建 `backend/tests/unit/workflow/test_state.py`
- 创建 `backend/tests/unit/workflow/test_prompts.py`

**执行步骤：**

- [ ] 先写状态对象与结构化输出解析测试
- [ ] 设计工作流状态字段与重试计数机制
- [ ] 固化意图识别、查询改写、方案生成的 Prompt 模板
- [ ] 为 Prompt 定义清晰的引用、风险和输出格式约束
- [ ] 跑通状态与 Prompt 测试并提交

**提交信息：**

```bash
git commit -m "feat: add workflow state and prompts"
```

### 任务 8：意图识别与查询改写节点

**涉及文件：**

- 创建 `backend/app/workflow/nodes/intent.py`
- 创建 `backend/app/workflow/nodes/rewrite.py`
- 创建 `backend/tests/unit/workflow/test_intent_node.py`
- 创建 `backend/tests/unit/workflow/test_rewrite_node.py`

**执行步骤：**

- [ ] 先写失败测试，验证结构化意图、情绪、实体输出
- [ ] 实现意图识别节点
- [ ] 先写查询改写失败测试，再实现标准化查询生成
- [ ] 确保不凭空补造事实
- [ ] 跑通节点测试并提交

**提交信息：**

```bash
git commit -m "feat: add intent and rewrite nodes"
```

### 任务 9：检索、重排与生成节点

**涉及文件：**

- 创建 `backend/app/workflow/nodes/retrieve.py`
- 创建 `backend/app/workflow/nodes/generate.py`
- 创建 `backend/tests/unit/workflow/test_retrieve_node.py`
- 创建 `backend/tests/unit/workflow/test_generate_node.py`

**执行步骤：**

- [ ] 先写检索节点失败测试，验证证据写回状态
- [ ] 实现检索节点与重排接入
- [ ] 先写生成节点失败测试，验证引用编号、结构化输出和风险提示
- [ ] 实现证据驱动方案生成
- [ ] 跑通节点测试并提交

**提交信息：**

```bash
git commit -m "feat: add retrieval and generation nodes"
```

### 任务 10：校验、路由与图编排

**涉及文件：**

- 创建 `backend/app/workflow/nodes/validate.py`
- 创建 `backend/app/workflow/routing.py`
- 创建 `backend/app/workflow/graph.py`
- 创建 `backend/tests/unit/workflow/test_validate_node.py`
- 创建 `backend/tests/unit/workflow/test_routing.py`
- 创建 `backend/tests/integration/workflow/test_graph.py`

**执行步骤：**

- [ ] 先写校验失败测试，覆盖引用缺失、结构不完整、无依据表述和高风险识别
- [ ] 实现校验节点
- [ ] 实现条件分支、重试上限与转人工逻辑
- [ ] 用 LangGraph 组装完整有向图
- [ ] 跑通工作流集成测试并提交

**提交信息：**

```bash
git commit -m "feat: compose complaint workflow graph"
```

---

## 分块二：接口、会话与事件流

### 任务 11：投诉会话 API 与仓储层

**涉及文件：**

- 创建 `backend/app/db/repositories/complaints.py`
- 创建 `backend/app/api/dependencies.py`
- 创建 `backend/app/api/v1/router.py`
- 创建 `backend/app/api/v1/complaints.py`
- 创建 `backend/tests/integration/api/test_sessions.py`

**执行步骤：**

- [ ] 先写失败的会话创建与查询测试
- [ ] 实现仓储层、依赖注入和投诉会话接口
- [ ] 支持幂等创建、状态查询和基础列表
- [ ] 跑通接口集成测试并提交

**提交信息：**

```bash
git commit -m "feat: add complaint session API"
```

### 任务 12：知识搜索与管理接口

**涉及文件：**

- 创建 `backend/app/db/repositories/knowledge.py`
- 创建 `backend/app/api/v1/knowledge.py`
- 创建 `backend/tests/integration/api/test_knowledge_search.py`

**执行步骤：**

- [ ] 先写失败的知识搜索测试
- [ ] 提供分页、来源过滤、业务类型过滤和关键字搜索
- [ ] 保证只返回脱敏快照
- [ ] 跑通知识接口测试并提交

**提交信息：**

```bash
git commit -m "feat: add knowledge search API"
```

### 任务 13：工作流服务编排层

**涉及文件：**

- 创建 `backend/app/workflow/service.py`
- 创建 `backend/tests/unit/workflow/test_service.py`
- 创建 `backend/tests/integration/workflow/test_service_integration.py`

**执行步骤：**

- [ ] 先写失败测试，验证会话启动、状态推进、节点异常处理和落库行为
- [ ] 实现工作流服务，对接仓储、网关和 LangGraph
- [ ] 让 API 层只负责输入输出，不直接持有业务流程逻辑
- [ ] 跑通服务层测试并提交

**提交信息：**

```bash
git commit -m "feat: wire complaint workflow service"
```

### 任务 14：可重放事件流与 SSE 接口

**涉及文件：**

- 创建 `backend/app/db/repositories/workflow_events.py`
- 修改 `backend/app/db/models/workflow.py`
- 创建 `backend/alembic/versions/0003_workflow_events.py`
- 修改 `backend/app/api/v1/complaints.py`
- 创建 `backend/tests/integration/api/test_message_stream.py`
- 创建 `backend/tests/integration/api/test_sse_reconnect.py`
- 创建 `docs/api/events.md`

**执行步骤：**

- [ ] 先写失败测试，验证事件持久化、断线重连和 `Last-Event-ID`
- [ ] 持久化 `workflow_started`、`intent_completed`、`retrieval_completed`、`generation_delta`、`validation_completed`、`human_review_required`、`workflow_completed`、`workflow_failed`
- [ ] 实现 `POST /messages` 和 `GET /events`
- [ ] 保证工作流执行与前端连接解耦
- [ ] 跑通消息流和重连测试并提交

**提交信息：**

```bash
git commit -m "feat: stream durable workflow events"
```

### 任务 15：人工反馈与工作流恢复接口

**涉及文件：**

- 创建 `backend/app/db/repositories/feedback.py`
- 创建 `backend/app/workflow/outbox.py`
- 修改 `backend/app/main.py`
- 修改 `backend/app/db/models/workflow.py`
- 创建 `backend/alembic/versions/0004_feedback_outbox.py`
- 创建 `backend/app/api/v1/feedback.py`
- 修改 `backend/app/api/v1/router.py`
- 创建 `backend/tests/integration/api/test_feedback.py`
- 创建 `backend/tests/integration/api/test_feedback_idempotency.py`

**执行步骤：**

- [ ] 先写失败测试，覆盖采纳、编辑、驳回以及幂等重复提交
- [ ] 使用 `Idempotency-Key` 与请求指纹实现反馈幂等
- [ ] 同事务内持久化反馈、最终方案和待恢复 outbox 记录
- [ ] 实现后台恢复 worker，支持进程重启后的待处理恢复
- [ ] 增加并发竞争场景测试，确保同一反馈只被处理一次
- [ ] 跑通反馈与恢复测试并提交

**提交信息：**

```bash
git commit -m "feat: add human review feedback loop"
```

---

## 分块三：前端工作台与用户交互

### 任务 16：Vue 工作台基础与会话状态

**涉及文件：**

- 创建 `frontend/index.html`
- 创建 `frontend/tsconfig.json`
- 创建 `frontend/vite.config.ts`
- 创建 `frontend/src/main.ts`
- 创建 `frontend/src/App.vue`
- 创建 `frontend/src/types/complaint.ts`
- 创建 `frontend/src/api/client.ts`
- 创建 `frontend/src/api/complaints.ts`
- 创建 `frontend/src/api/sse.ts`
- 创建 `frontend/src/stores/complaint.ts`
- 创建 `frontend/src/views/ComplaintWorkbench.vue`
- 创建 `frontend/tests/unit/complaint-store.test.ts`

**执行步骤：**

- [ ] 安装锁定版本的前端依赖并生成 `package-lock.json`
- [ ] 先写失败的 Store 测试，覆盖会话创建、事件归约、流式文本拼接、错误状态、归档与重置
- [ ] 实现类型化 API 客户端与 Pinia Store
- [ ] 由 Store 独占状态与事件归约，组件只通过 `props` 与 `emit` 交互
- [ ] 完成工作台骨架布局
- [ ] 运行单元测试、类型检查并提交

**提交信息：**

```bash
git commit -m "feat: add complaint workbench state"
```

### 任务 17：工作台组件与流式交互

**涉及文件：**

- 创建 `frontend/src/components/SessionSidebar.vue`
- 创建 `frontend/src/components/ComplaintComposer.vue`
- 创建 `frontend/src/components/WorkflowTimeline.vue`
- 创建 `frontend/src/components/SolutionPanel.vue`
- 创建 `frontend/src/components/EvidencePanel.vue`
- 创建 `frontend/src/components/FeedbackBar.vue`
- 修改 `frontend/src/views/ComplaintWorkbench.vue`
- 创建 `frontend/tests/unit/ComplaintWorkbench.test.ts`
- 创建 `frontend/tests/e2e/complaint-flow.spec.ts`
- 创建 `frontend/playwright.config.ts`
- 创建 `frontend/tests/mock-api/server.mjs`

**执行步骤：**

- [ ] 先写失败的组件集成测试，覆盖投诉提交、阶段事件、证据展示、流式方案、风险提示和反馈动作
- [ ] 实现可访问性良好的组件，包含加载、空态、错误态和固定面板布局
- [ ] 实现采纳、编辑后采纳、驳回交互
- [ ] 构建确定性浏览器测试所需的模拟 API
- [ ] 跑通 `Playwright` 快乐路径测试
- [ ] 执行 `npm test`、`npm run type-check`、`npm run build` 并提交

**提交信息：**

```bash
git commit -m "feat: complete complaint handling workbench"
```

---

## 分块四：评估、部署与交付

### 任务 18：指标与离线评估

**涉及文件：**

- 创建 `backend/app/observability/metrics.py`
- 创建 `backend/app/evaluation/dataset.py`
- 创建 `backend/app/evaluation/retrieval_metrics.py`
- 创建 `backend/app/evaluation/business_metrics.py`
- 创建 `backend/app/evaluation/performance.py`
- 创建 `backend/app/evaluation/runner.py`
- 创建 `backend/app/api/v1/metrics.py`
- 修改 `backend/app/api/v1/router.py`
- 创建 `backend/scripts/run_evaluation.py`
- 创建 `backend/tests/unit/evaluation/test_retrieval_metrics.py`
- 创建 `backend/tests/unit/evaluation/test_business_metrics.py`
- 创建 `backend/tests/performance/run_load.py`
- 创建 `backend/tests/integration/api/test_metrics.py`
- 创建 `data/evaluation/sample.jsonl`
- 创建 `data/evaluation/acceptance.jsonl`
- 创建 `docs/evaluation/README.md`

**执行步骤：**

- [ ] 先写失败的指标测试，覆盖意图准确率、`Recall@5`、前 `3` 证据命中率、引用完整率、无依据表述占比、采纳率、平均处理时长、API 成功率、百分位统计与空数据集行为
- [ ] 实现纯函数化指标计算，保持确定性
- [ ] 实现评估执行器，记录数据集版本、模型版本、Prompt 版本、知识版本、工作流版本、时间戳与硬件说明
- [ ] 准备 `120` 条带覆盖标签的验收数据集，以及用于冒烟的小样本数据集
- [ ] 暴露 `/api/v1/metrics/summary` 与 `/metrics`
- [ ] 运行评估测试、样例评估、验收评估与可重复性能测试
- [ ] 产出 `JSON` 与 `Markdown` 报告并提交

**提交信息：**

```bash
git commit -m "feat: add observable evaluation pipeline"
```

### 任务 19：Docker Compose 与类生产本地环境

**涉及文件：**

- 修改 `docker-compose.yml`
- 创建 `backend/Dockerfile`
- 创建 `frontend/Dockerfile`
- 创建 `infra/mysql/init.sql`
- 创建 `infra/prometheus/prometheus.yml`
- 创建 `backend/tests/stubs/model_server.py`
- 创建 `docs/deployment/local.md`
- 创建 `docs/deployment/private-models.md`
- 创建 `backend/tests/contract/test_service_health.py`

**执行步骤：**

- [ ] 先写失败的服务编排测试，验证 `api`、`frontend`、`model-stub`、`mysql`、`redis`、`milvus`、`etcd`、`minio`、`elasticsearch`、`prometheus` 全部存在
- [ ] 为服务补齐健康检查、命名卷、网络与启动依赖
- [ ] 用 `.env` 驱动环境配置，不默认下载真实模型
- [ ] 为 `model-stub` 提供支持 `LLM`、嵌入和重排的确定性 HTTP 桩服务
- [ ] 文档化三种部署模式：开发假模型、联调测试服务、生产私有模型端点
- [ ] 启动基础设施并执行契约测试
- [ ] 完善本地部署文档并提交

**提交信息：**

```bash
git commit -m "ops: add production-like local stack"
```

### 任务 20：端到端验证与交付文档

**涉及文件：**

- 创建 `backend/tests/integration/test_end_to_end_complaint.py`
- 创建 `frontend/tests/e2e/degraded-flow.spec.ts`
- 创建 `scripts/verify.ps1`
- 创建 `scripts/verify-stack.ps1`
- 创建 `docs/evaluation/mvp-acceptance.md`
- 修改 `README.md`

**执行步骤：**

- [ ] 先写后端端到端验收测试，覆盖会话创建、投诉提交、意图与证据事件、引用校验、人工复核、反馈提交与最终状态落库
- [ ] 先写降级流浏览器测试，覆盖 `Milvus` 降级、双检索失效、重连、重复事件和 `workflow_failed`
- [ ] 实现一键验证脚本：`verify.ps1` 负责确定性套件，`verify-stack.ps1` 负责完整本地栈
- [ ] 跑通后端单元/集成、前端单元/类型/构建、浏览器测试、契约测试和本地栈测试
- [ ] 完成验收报告，记录模型模式、硬件、实测延迟、检索指标、引用完整率、已知限制和偏差说明
- [ ] 核验依赖来源表，若存在 `2026-04-30` 之后发布的运行时依赖则验收失败
- [ ] 完成最终提交

**提交信息：**

```bash
git commit -m "test: verify suzhida mvp workflow"
```

---

## 6. 执行铁律

- 所有行为变更都必须遵循 `$test-driven-development`：先写失败测试，再补最小实现，再复跑验证。
- 只要测试出现非预期失败，就使用 `$systematic-debugging` 先追根因，不允许围绕现象打补丁。
- 每个任务完成后都应进行 `$requesting-code-review`。
- 每个分块声明完成前，都必须执行 `$verification-before-completion`。
- 生产服务必须继续通过类型化网关保持可替换性。
- 单元测试和确定性集成测试不得依赖外网或 GPU。
- 任何性能结论都必须附带硬件、模型、量化方式、数据集、并发数、上下文长度和测试命令。
- 本 MVP 范围内不启动 `LoRA` 微调、生产级 `Kubernetes`、自动结案和多智能体重构。

## 7. 完成定义

当且仅当满足以下条件时，项目可视为达到上线交付前的完整状态：

- 网页工作台可完成投诉输入、流式观察、证据查看、人工反馈和归档。
- LangGraph 工作流具备有限重试、条件分支、降级和人工兜底。
- `Milvus + Elasticsearch + Redis` 混合检索链路可运行。
- 所有生成方案都能展示真实可追溯引用。
- 评估、监控、性能和验收文档完整。
- `verify.ps1` 与 `verify-stack.ps1` 可重复运行。
- 本地 `Docker Compose` 栈与私有模型接入说明完整。
- 文档、脚本、接口、数据与测试结果都保持中文说明，技术名词保留必要原文标识。
