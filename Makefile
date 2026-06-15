.PHONY: backend-test backend-lint frontend-test test up down

backend-test:
	Push-Location backend; ..\.venv\Scripts\python.exe -m pytest -q; Pop-Location

backend-lint:
	Push-Location backend; ..\.venv\Scripts\python.exe -m ruff check app tests; ..\.venv\Scripts\python.exe -m mypy app; Pop-Location

frontend-test:
	Push-Location frontend; npm test; Pop-Location

test: backend-test frontend-test

up:
	docker compose up -d --wait

down:
	docker compose down --volumes
