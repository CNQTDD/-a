# 项目协作说明

## 项目概述

诉智达（`suzhida`）是一个投诉智能处置与闭环管理系统。系统采用“单智能体 + LangGraph 状态机 + 局部循环”的架构，通过检索增强生成帮助客服坐席更快处理投诉。

## 技术决策

- 后端采用测试驱动开发，先写失败测试，再补最小实现。
- 所有外部服务（`Milvus`、`Elasticsearch`、`Redis`、`vLLM`）都通过适配器接口隔离，单元测试使用确定性假实现。
- LangGraph 工作流状态机负责流程编排，业务逻辑放在独立节点函数中。
- 前端由 `Pinia` 状态仓库持有全部状态，组件只通过 `props` 接收数据、通过 `emit` 发送指令。

## 常用命令

```powershell
# 后端测试
Push-Location backend; ..\.venv\Scripts\python.exe -m pytest -q; Pop-Location

# 后端静态检查
Push-Location backend; ..\.venv\Scripts\python.exe -m ruff check app tests; Pop-Location

# 前端测试
Push-Location frontend; npm test; Pop-Location

# 前端类型检查
Push-Location frontend; npm run type-check; Pop-Location
```
