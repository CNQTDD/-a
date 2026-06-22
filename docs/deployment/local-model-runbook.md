# 本地模型联调运行手册

本文档适用于以下路径：基础设施仍通过 `Docker Compose` 启动，而私有模型服务运行在 Windows 宿主机上。

目标机器假设：

- 系统内存：`32 GB`
- 显存：`12 GB`
- 用途：本地功能联调
- 并发要求：仅低并发验证

推荐模型组合：

- 大模型：`Qwen2.5-7B-Instruct`
- 嵌入模型：`BAAI/bge-m3`
- 重排模型：`BAAI/bge-reranker-v2-m3`

## 一、接口契约

应用侧依赖三个 HTTP 服务。

### 1. 大模型接口

基准地址示例：

```text
http://127.0.0.1:8001/v1
```

最少需要支持 `OpenAI` 风格的 `/v1/chat/completions`。

返回内容至少要能覆盖：

- 意图识别 JSON
- 方案生成文本
- 流式输出

### 2. 嵌入接口

基准地址示例：

```text
http://127.0.0.1:8002/v1
```

最少需要支持 `/v1/embeddings`。

### 3. 重排接口

基准地址示例：

```text
http://127.0.0.1:8003/v1
```

最少需要支持 `/v1/rerank`，并返回分值结果。

## 二、宿主机启动建议

仓库内不包含真实模型权重，请使用你们内部已经审批的私有制品。

### 大模型服务

建议起步参数：

- 模型：`Qwen2.5-7B-Instruct`
- 量化：`INT4`
- 上下文长度：`4096`
- `max_num_seqs`：`4`
- 显存利用率：`0.85` 到 `0.90`

在连接后端前，先手工发送一条短请求做预热。

### 嵌入服务

建议单独运行 `BAAI/bge-m3` 服务。

如果显存紧张，可以先放到 CPU 上。

### 重排服务

建议单独运行 `BAAI/bge-reranker-v2-m3` 服务。

如果显存紧张，也可以先放到 CPU 上。

## 三、环境配置

从 [`.env.local-gpu.example`](D:/项目/suzhida/.env.local-gpu.example) 复制本地配置，确认以下变量：

```text
LLM_BASE_URL=http://host.docker.internal:8001/v1
EMBEDDING_BASE_URL=http://host.docker.internal:8002/v1
RERANKER_BASE_URL=http://host.docker.internal:8003/v1
LLM_MODEL=Qwen2.5-7B-Instruct
EMBEDDING_MODEL=BAAI/bge-m3
RERANKER_MODEL=BAAI/bge-reranker-v2-m3
```

## 四、启动前检查

在启动 Compose 栈之前，先确认三个模型接口都可访问。

### 1. 大模型接口检查

```powershell
$body = @{
  model = "Qwen2.5-7B-Instruct"
  messages = @(
    @{ role = "system"; content = "intent classification" }
    @{ role = "user"; content = "套餐被重复扣费，请核查并退回多扣部分。" }
  )
  response_format = @{ type = "json_object" }
} | ConvertTo-Json -Depth 6

Invoke-RestMethod -Method Post -Uri "http://127.0.0.1:8001/v1/chat/completions" -ContentType "application/json" -Body $body
```

### 2. 嵌入接口检查

```powershell
$body = @{
  model = "BAAI/bge-m3"
  input = @("重复扣费投诉", "账单核查")
} | ConvertTo-Json -Depth 4

Invoke-RestMethod -Method Post -Uri "http://127.0.0.1:8002/v1/embeddings" -ContentType "application/json" -Body $body
```

### 3. 重排接口检查

```powershell
$body = @{
  model = "BAAI/bge-reranker-v2-m3"
  query = "重复扣费投诉"
  documents = @("资费规则条款", "退款流程条款")
} | ConvertTo-Json -Depth 4

Invoke-RestMethod -Method Post -Uri "http://127.0.0.1:8003/v1/rerank" -ContentType "application/json" -Body $body
```

## 五、启动 Compose 栈

本模式下不要启动 `model-stub`。

```powershell
docker compose --profile development up -d --wait api frontend mysql redis etcd minio milvus elasticsearch prometheus
```

## 六、初始化应用

### 1. 执行数据库迁移

```powershell
docker compose exec -T api alembic upgrade head
```

### 2. 导入样例知识

```powershell
docker compose exec -T api python scripts/seed_sample_knowledge.py `
  --database-url mysql+pymysql://suzhida:suzhida@mysql:3306/suzhida `
  --elasticsearch-url http://elasticsearch:9200 `
  --milvus-uri http://milvus:19530
```

## 七、烟测步骤

### 1. 接口健康检查

```powershell
Invoke-RestMethod "http://127.0.0.1:8000/health"
```

预期结果：

```json
{"service":"suzhida-api","status":"ok"}
```

### 2. 前端页面检查

打开：

```text
http://127.0.0.1:5280
```

提交一条计费类投诉后，确认：

1. 工作流时间线能够向前推进
2. 右侧证据面板能够展示检索结果
3. 系统能够生成处置建议
4. 最终状态进入人工复核，而不是自动结案

## 八、内存不足时的降载顺序

1. 先降低 `max_num_seqs`
2. 再缩短大模型上下文长度
3. 把嵌入服务迁移到 CPU
4. 把重排服务迁移到 CPU
5. 本地人工联调时临时关闭 `Prometheus`

在没有明确测量证据之前，不要继续压缩 `Elasticsearch` 堆内存。

## 九、停止服务

```powershell
docker compose down --remove-orphans
```
