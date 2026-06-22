# 真实投诉语义升级 Implementation Plan

> **For agentic workers:** REQUIRED: Use $subagent-driven-development (if subagents available) or $executing-plans to implement this plan. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 让系统能够识别并处置“网络异常影响炒股导致损失要求赔偿”这类真实高风险投诉，输出符合业务边界的方案与人工复核路由。

**Architecture:** 沿用现有 FastAPI + 工作流服务 + 检索规则的技术栈，不引入新框架。先用测试锁定模型桩、工作流本地回退和知识规则三个关键点，再以最小改动补齐高风险意图识别、检索命中与处置建议生成。

**Tech Stack:** Python 3.11、FastAPI、SQLAlchemy 2、pytest、Elasticsearch、现有 model-stub 与本地工作流回退逻辑

---

## Chunk 1: 真实投诉识别与路由

### Task 1: 补齐模型桩的真实场景失败测试

**Files:**
- Modify: `backend/tests/unit/stubs/test_model_server.py`
- Test: `backend/tests/unit/stubs/test_model_server.py`

- [ ] **Step 1: 写失败测试**

```python
def test_model_stub_classifies_network_loss_compensation_as_high_risk() -> None:
    ...
```

- [ ] **Step 2: 运行测试确认失败**

Run: `Push-Location backend; ..\\.venv-codex\\Scripts\\python.exe -m pytest tests/unit/stubs/test_model_server.py -q; Pop-Location`
Expected: FAIL，原因是当前桩服务仍返回 `billing_dispute`

- [ ] **Step 3: 写最小实现**

```python
if "网络" in user_text and "赔偿" in user_text:
    return {
        "intent": "service_outage_compensation",
        "risk_level": "high",
        ...
    }
```

- [ ] **Step 4: 复跑测试确认通过**

Run: `Push-Location backend; ..\\.venv-codex\\Scripts\\python.exe -m pytest tests/unit/stubs/test_model_server.py -q; Pop-Location`
Expected: PASS

### Task 2: 补齐工作流服务的真实场景失败测试

**Files:**
- Modify: `backend/tests/unit/workflow/test_service.py`
- Test: `backend/tests/unit/workflow/test_service.py`

- [ ] **Step 1: 写失败测试**

```python
@pytest.mark.asyncio
async def test_start_run_marks_network_loss_claim_for_high_risk_human_review(...):
    ...
```

- [ ] **Step 2: 运行测试确认失败**

Run: `Push-Location backend; ..\\.venv-codex\\Scripts\\python.exe -m pytest tests/unit/workflow/test_service.py -q; Pop-Location`
Expected: FAIL，原因是当前事件与方案仍是账单纠纷路径

- [ ] **Step 3: 写最小实现**

```python
session.risk_level = "high"
solution.validation_details["recommended_route"] = "senior_human_review"
```

- [ ] **Step 4: 复跑测试确认通过**

Run: `Push-Location backend; ..\\.venv-codex\\Scripts\\python.exe -m pytest tests/unit/workflow/test_service.py -q; Pop-Location`
Expected: PASS

### Task 3: 实现模型桩与本地回退的真实投诉识别

**Files:**
- Modify: `backend/tests/stubs/model_server.py`
- Modify: `backend/app/workflow/service.py`
- Test: `backend/tests/unit/stubs/test_model_server.py`
- Test: `backend/tests/unit/workflow/test_service.py`

- [ ] **Step 1: 最小实现模型桩的分支识别**
- [ ] **Step 2: 最小实现 `_LocalLLMGateway` 的相同分支识别**
- [ ] **Step 3: 为高风险赔损诉求生成谨慎方案**
- [ ] **Step 4: 运行相关单测**

Run: `Push-Location backend; ..\\.venv-codex\\Scripts\\python.exe -m pytest tests/unit/stubs/test_model_server.py tests/unit/workflow/test_service.py -q; Pop-Location`
Expected: PASS

## Chunk 2: 知识规则与端到端场景

### Task 4: 补齐知识规则的真实场景覆盖

**Files:**
- Modify: `data/samples/rules.md`
- Modify: `backend/scripts/seed_sample_knowledge.py`
- Modify: `backend/tests/unit/scripts/test_seed_sample_knowledge.py`
- Test: `backend/tests/unit/scripts/test_seed_sample_knowledge.py`

- [ ] **Step 1: 先写失败测试，要求新规则章节被识别并归类到服务处置**
- [ ] **Step 2: 运行测试确认失败**

Run: `Push-Location backend; ..\\.venv-codex\\Scripts\\python.exe -m pytest tests/unit/scripts/test_seed_sample_knowledge.py -q; Pop-Location`
Expected: FAIL，原因是当前规则映射不包含网络故障赔损场景

- [ ] **Step 3: 补充中文业务规则**

```text
网络异常与损失赔付规则
- 不得直接承诺证券交易损失赔偿
- 先核查故障时段、影响范围、用户证据
- 高风险诉求转人工复核/法务支持
```

- [ ] **Step 4: 更新规则标题到 business_type 映射**
- [ ] **Step 5: 复跑测试确认通过**

### Task 5: 补齐端到端真实投诉场景失败测试

**Files:**
- Modify: `backend/tests/integration/test_end_to_end_complaint.py`
- Test: `backend/tests/integration/test_end_to_end_complaint.py`

- [ ] **Step 1: 新增真实投诉场景失败测试**
- [ ] **Step 2: 运行测试确认失败**

Run: `Push-Location backend; ..\\.venv-codex\\Scripts\\python.exe -m pytest tests/integration/test_end_to_end_complaint.py -q; Pop-Location`
Expected: FAIL，原因是当前返回的意图、风险等级或方案文本不符合真实场景

- [ ] **Step 3: 以最小代码补齐服务输出**
- [ ] **Step 4: 复跑测试确认通过**

### Task 6: 记录问题并完成阶段验证

**Files:**
- Modify: `docs/evaluation/2026-06-18-最终复验问题记录.md`

- [ ] **Step 1: 记录本次问题、根因、修改点与验证结果**
- [ ] **Step 2: 运行本次聚焦验证**

Run: `Push-Location backend; ..\\.venv-codex\\Scripts\\python.exe -m pytest tests/unit/stubs/test_model_server.py tests/unit/workflow/test_service.py tests/unit/scripts/test_seed_sample_knowledge.py tests/integration/test_end_to_end_complaint.py -q; Pop-Location`
Expected: PASS

- [ ] **Step 3: 运行更完整复验**

Run: `powershell -ExecutionPolicy Bypass -File .\\scripts\\verify.ps1`
Expected: 现有后端/前端基础验证保持通过

