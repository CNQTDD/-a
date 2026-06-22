# 上线巡检清单

本文档用于诉智达在“本地跑通之后、正式上线之前”的最后一轮人工巡检。

## 一、版本与环境

- [ ] 当前部署分支、提交号和交付包版本已记录
- [ ] 私有模型名称、制品版本、量化格式已记录
- [ ] 生产环境 `LLM_BASE_URL`、`EMBEDDING_BASE_URL`、`RERANKER_BASE_URL` 已配置为真实地址
- [ ] 数据库、Redis、Milvus、Elasticsearch、MinIO 的连接信息已核对

## 二、数据库与知识库

- [ ] 已执行 `alembic upgrade head`
- [ ] 样例知识或生产知识已成功导入
- [ ] MySQL 唯一约束检查通过
- [ ] Milvus 集合可查询
- [ ] Elasticsearch 索引状态正常

## 三、服务健康

- [ ] `GET /health` 返回正常
- [ ] 前端首页可打开
- [ ] 后端日志无持续报错
- [ ] 模型网关连通性正常
- [ ] `/metrics` 可抓取

## 四、功能烟测

- [ ] 新建投诉会话成功
- [ ] 启动处置流程时出现确认弹窗
- [ ] 同一未归档投诉重复提交时复用原会话
- [ ] 时间线能看到意图、情绪、实体、校验和异常信息
- [ ] 证据面板能显示证据或清晰提示无证据
- [ ] 方案面板能显示流式或最终处置建议
- [ ] 采纳、编辑后采纳、驳回、归档都可用
- [ ] 高风险或失败场景能进入人工兜底

## 五、回归验证

- [ ] `powershell -ExecutionPolicy Bypass -File scripts/verify.ps1` 通过
- [ ] `powershell -ExecutionPolicy Bypass -File scripts/verify-stack.ps1` 通过
- [ ] `powershell -ExecutionPolicy Bypass -File scripts/post-deploy-check.ps1` 通过
- [ ] 当前验收报告、问题记录与 `Task1` 到 `Task20` 最终复验清单已经同步到最新结果

## 六、运维准备

- [ ] 监控面板或 Prometheus 抓取项已确认
- [ ] 常见故障处理人和升级路径已明确
- [ ] 日志保留和数据备份策略已确认
- [ ] 回滚方案已准备

## 七、禁止项

以下情况任一未满足，都不应宣布上线完成：

- 使用假地址或空地址连接私有模型
- 未完成数据库迁移
- 只跑单测、没有跑全栈验证
- 只验证 happy path，没有验证反馈和归档
- 没有更新验收文档却直接对外宣称完成
