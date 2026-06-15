# AGENTS.md

## 项目概述

诉智达（suzhida）是一个投诉智能处置与闭环管理系统。系统采用"单 Agent + LangGraph 状态机 + 局部循环"的架构，通过检索增强生成（RAG）帮助客服坐席快速处理投诉。

## 技术决策

- 后端采用 TDD（测试驱动开发），先写失败的测试再实现
- 所有外部服务（Milvus、ES、Redis、vLLM）都通过适配器接口隔离，单元测试使用确定性 fake
- LangGraph 工作流状态机负责流程编排，业务逻辑放在独立的节点函数中
- 前端 Pinia store 持有所有状态，组件只通过 props 获取数据、通过 emit 发送指令

## 常用命令

```powershell
# 后端测试
Push-Location backend; ..\.venv\Scripts\python.exe -m pytest -q; Pop-Location

# 后端 lint
Push-Location backend; ..\.venv\Scripts\python.exe -m ruff check app tests; Pop-Location

# 前端测试
Push-Location frontend; npm test; Pop-Location

# 前端类型检查
Push-Location frontend; npm run type-check; Pop-Location
```
