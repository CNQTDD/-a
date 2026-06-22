# 评估说明

本目录用于保存诉智达 MVP 的离线评估数据、验收报告和可重复执行的评估产物。

## 数据集

- `data/evaluation/sample.jsonl`：用于冒烟验证的小样本数据集。
- `data/evaluation/acceptance.jsonl`：用于验收评估的数据集。

## 执行脚本

使用 `backend/scripts/run_evaluation.py` 生成 `JSON` 报告和 `Markdown` 报告。
端到端验收记录位于 `docs/evaluation/mvp-acceptance.md`。
本轮最终交付材料还包括：
- `docs/evaluation/2026-06-18-最终复验问题记录.md`
- `docs/evaluation/2026-06-22-task1-task20-最终复验清单.md`

示例命令：

```powershell
Push-Location backend
try {
  ..\.venv-codex\Scripts\python.exe scripts\run_evaluation.py `
    --dataset ..\data\evaluation\sample.jsonl `
    --mode smoke `
    --output-dir artifacts\evaluation
} finally {
  Pop-Location
}
```
