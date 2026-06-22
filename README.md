# 诉智达

诉智达是一个面向客服与运营坐席的投诉智能处置与闭环管理系统。项目采用“单智能体 + LangGraph 状态机 + 混合检索 + Vue 工作台”的架构，目标是在本地可重复部署的前提下，跑通投诉理解、证据检索、方案生成、人工反馈和事件闭环全链路。

## 当前状态

截至 `2026-06-22`，项目已经完成本地 MVP 主链路验证：

- 后端单元与集成测试通过：`104 passed, 5 skipped`
- 前端单元测试通过：`17 passed`
- 前端类型检查通过
- 前端生产构建通过
- Docker Compose 全栈验证通过
- 基础设施契约测试通过：`9 passed`
- 后端端到端测试通过：`2 passed`
- 前端 Playwright 端到端测试通过：`2 passed`

这意味着前端、后端、FastAPI 接口、SSE 事件流、本地 Docker 栈和样例知识检索链路都已经实际跑通，而不只是 demo。

## 访问地址

- Docker Compose 前端工作台：`http://127.0.0.1:5280`
- Docker Compose 后端接口：`http://127.0.0.1:8000`
- 本地 Vite 开发服务：`http://127.0.0.1:4173`
- Playwright 使用的模拟 API：`http://127.0.0.1:5184`

## 快速验证

在仓库根目录执行：

```powershell
powershell -ExecutionPolicy Bypass -File scripts/verify.ps1
powershell -ExecutionPolicy Bypass -File scripts/verify-stack.ps1
```

说明：

- `verify.ps1` 用于代码级验证，覆盖后端测试、前端单测、类型检查和前端构建。
- `verify-stack.ps1` 用于运行态验证，覆盖 Docker Compose、本地样例知识播种、基础设施契约、后端端到端、前端 Playwright 端到端和负载脚本。

## 本地部署说明

推荐优先使用“确定性验证模式”进行日常开发和复验：

- 参考 [本地部署说明](D:/项目/suzhida/docs/deployment/local.md)
- 本地真实模型联调参考 [本地模型联调运行手册](D:/项目/suzhida/docs/deployment/local-model-runbook.md)
- 私有模型分档与切换策略参考 [私有模型部署档位](D:/项目/suzhida/docs/deployment/private-models.md)
- 上线前巡检参考 [上线巡检清单](D:/项目/suzhida/docs/deployment/go-live-checklist.md)
- 运维排障参考 [运维异常处置手册](D:/项目/suzhida/docs/deployment/operations-runbook.md)

## 技术栈

- 后端：`Python 3.11`、`FastAPI`、`Pydantic v2`、`SQLAlchemy 2`、`Alembic`、`LangGraph`
- 检索与存储：`MySQL 8`、`Redis`、`Milvus`、`Elasticsearch`、`MinIO`
- 前端：`Vue 3`、`TypeScript`、`Vite`、`Pinia`
- 测试：`pytest`、`Vitest`、`Playwright`
- 部署：`Docker Compose`、`Prometheus`

## 目录说明

```text
.
├── backend/                  后端服务、工作流、检索与测试
├── frontend/                 前端工作台、组件与浏览器测试
├── data/                     样例知识与评估数据
├── docs/                     设计、计划、部署与验收文档
├── infra/                    基础设施初始化与监控配置
└── scripts/                  一键验证与辅助脚本
```

## 交付说明

当前仓库已经达到“单机可重复部署、模块可联动、可进行本地交付验收”的状态。

如果要进一步进入生产发布阶段，仍建议在私有模型、生产数据库、生产监控和运维流程上再做一次环境级收口，重点包括：

- 私有模型真实吞吐压测
- 生产机房网络与鉴权接入
- 监控告警联动
- 运维值守与异常处置流程
