# Evaluation

This directory records offline evaluation artifacts for the Suzhida MVP.

## Datasets

- `data/evaluation/sample.jsonl` is a small smoke fixture.
- `data/evaluation/acceptance.jsonl` contains the 120-case acceptance set.

## Runner

Use `backend/scripts/run_evaluation.py` to generate JSON and Markdown reports.

The end-to-end acceptance record lives in `docs/evaluation/mvp-acceptance.md`.

Example:

```powershell
Push-Location backend
try {
  ..\.venv-codex\Scripts\python.exe scripts\run_evaluation.py --dataset ..\data\evaluation\sample.jsonl --mode smoke --output-dir artifacts\evaluation
} finally {
  Pop-Location
}
```
