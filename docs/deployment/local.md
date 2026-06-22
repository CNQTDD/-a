# 本地部署说明

诉智达支持两种本地部署模式：

1. 确定性验证模式
2. 单机真实模型联调模式

默认推荐使用“确定性验证模式”。它启动更快、结果更稳定，也不会自动下载或依赖外部生产模型制品。

## 模式一：确定性验证模式

该模式用于日常开发、回归测试和交付前复验。

### 组成服务

- `api`
- `frontend`
- `model-stub`
- `mysql`
- `redis`
- `etcd`
- `minio`
- `milvus`
- `elasticsearch`
- `prometheus`

### 启动命令

```powershell
docker compose --profile development up -d --wait api frontend model-stub mysql redis etcd minio milvus elasticsearch prometheus
```

### 适用场景

- 前后端日常联调
- 样例知识链路验证
- 单元测试之外的本地运行检查
- 执行 `scripts/verify-stack.ps1`

## 模式二：单机真实模型联调模式

该模式保留 Docker Compose 基础设施，但将模型服务切换为宿主机上的私有接口。

### 适用硬件

- 系统内存：`32 GB`
- 显存：`12 GB`
- 目标用途：功能联调和低并发业务演示

### 推荐资源分配

- `Docker Desktop` 内存：`14 GB` 到 `16 GB`
- `Docker Desktop` CPU：`10` 到 `12` 核
- 为 Windows、浏览器和宿主机模型服务保留至少 `12 GB` 主机内存

### 推荐服务拆分

Docker Compose 内运行：

- `api`
- `frontend`
- `mysql`
- `redis`
- `etcd`
- `minio`
- `milvus`
- `elasticsearch`
- `prometheus`

宿主机内运行：

- `Qwen2.5-7B-Instruct` 的 `vLLM` 服务
- `BAAI/bge-m3` 嵌入服务
- `BAAI/bge-reranker-v2-m3` 重排服务

说明：

- 本模式下不要启动 `model-stub` 容器。
- 本地测试阶段优先使用 `Qwen2.5-7B-Instruct`，生产再切换到 `Qwen2.5-14B-Instruct`。

### 环境变量

建议从 `.env.local-gpu.example` 复制出本地配置。

至少需要配置：

```text
LLM_BASE_URL=http://host.docker.internal:8001/v1
EMBEDDING_BASE_URL=http://host.docker.internal:8002/v1
RERANKER_BASE_URL=http://host.docker.internal:8003/v1
```

### 启动命令

```powershell
docker compose --profile development up -d --wait api frontend mysql redis etcd minio milvus elasticsearch prometheus
```

## 推荐验证顺序

1. 先启动宿主机模型服务
2. 手工检查模型健康接口可用
3. 启动 Docker Compose 基础设施和应用服务
4. 执行数据库迁移
5. 导入样例知识
6. 打开 `http://127.0.0.1:5280` 进行页面联调

更详细步骤见 [本地模型联调运行手册](D:/项目/suzhida/docs/deployment/local-model-runbook.md)。

## 避免 OOM 的建议

- 不要在 `12 GB` 显存的本地测试机上直接加载 `Qwen2.5-14B`
- 本地优先使用已经验证过的 `INT4` 制品
- 上下文长度先控制在 `4096`
- `max_num_seqs` 建议从 `4` 起步，通常不要超过 `8`
- 显存紧张时优先把嵌入和重排服务迁移到 CPU
- 在没有明确测量证据前，不要继续压缩 `Elasticsearch` 的堆内存配置
