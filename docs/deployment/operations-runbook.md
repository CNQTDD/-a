# 运维异常处置手册

本文档用于诉智达上线后的常见异常排查、临时处置和回滚说明。

## 一、常见入口

- 前端工作台：`http://127.0.0.1:5280`
- 后端健康检查：`http://127.0.0.1:8000/health`
- Prometheus 指标：`http://127.0.0.1:8000/metrics`
- 部署后巡检脚本：`powershell -ExecutionPolicy Bypass -File scripts/post-deploy-check.ps1`

## 二、异常处置

### 1. 前端能打开，但启动处置流程无响应

优先检查：

1. 浏览器是否出现“确认启动处置流程”弹窗
2. 后端 `POST /api/v1/complaints/sessions` 是否成功
3. 后端 `POST /api/v1/complaints/{session_id}/messages` 是否成功
4. SSE `GET /events` 是否正常返回事件

临时处置：

- 先执行 `scripts/post-deploy-check.ps1`
- 再查看 `docker compose logs api frontend --tail 200`
- 如只影响单个会话，先切回人工坐席处理

### 2. 证据面板一直为空

优先检查：

1. 样例或生产知识是否已导入
2. Elasticsearch 索引是否健康
3. Milvus 集合是否已加载
4. 当前会话是否进入了降级模式

临时处置：

- 执行知识导入或重建索引
- 如 Milvus 不可用，确认是否已切入单路检索降级
- 高风险投诉优先人工兜底

### 3. 工作流进入失败状态

典型现象：

- 时间线显示“处理失败”
- 顶部提示出现“流程转入人工兜底”

处置建议：

1. 先记录当前投诉会话 ID
2. 查看 `api` 容器日志中的工作流异常原因
3. 检查模型网关、Milvus、Elasticsearch 和 Redis 状态
4. 由坐席转人工继续处理，避免阻塞用户

### 4. 反馈提交失败

优先检查：

1. 后端 `/feedback` 接口是否返回错误
2. 是否存在数据库写入异常
3. 是否有幂等键冲突或重复提交

临时处置：

- 不要重复快速点击
- 保留失败提示截图和会话 ID
- 确认后端恢复后再次提交一次

## 三、基础设施巡检

### Docker Compose

```powershell
docker compose ps
docker compose logs api --tail 200
docker compose logs frontend --tail 200
docker compose logs milvus --tail 200
docker compose logs elasticsearch --tail 200
```

### 数据库迁移状态

```powershell
docker compose exec -T api alembic current
docker compose exec -T api alembic heads
```

### 样例知识重导入

```powershell
docker compose exec -T api python scripts/seed_sample_knowledge.py `
  --database-url mysql+pymysql://suzhida:suzhida@mysql:3306/suzhida `
  --elasticsearch-url http://elasticsearch:9200 `
  --milvus-uri http://milvus:19530
```

## 四、监控与值守建议

- 至少关注 `api`、`frontend`、`mysql`、`redis`、`milvus`、`elasticsearch` 状态
- 监控中应包含接口错误率、响应时延和进程资源占用
- 高风险投诉和失败会话要有人工接手机制
- 每次发布后都执行一次 `scripts/post-deploy-check.ps1`

## 五、回滚

满足以下任一情况，应优先考虑回滚：

- 发布后核心流程无法创建会话
- 大面积无法提交反馈
- 模型网关配置错误且无法快速恢复
- 数据库迁移后出现结构不兼容问题

回滚原则：

1. 先停止新的业务写入
2. 切回上一个已验证通过的镜像或发布包
3. 保留本次异常日志、会话 ID 和巡检报告
4. 重新执行 `scripts/post-deploy-check.ps1`

## 六、交接要求

- 当班人员需记录异常时间、会话 ID、影响范围和已采取动作
- 若升级给开发或平台侧，必须附上日志片段和巡检结果
- 不要只描述“页面有问题”，要明确是前端、接口、检索还是模型链路异常
