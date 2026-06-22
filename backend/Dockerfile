FROM python:3.11-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

WORKDIR /app

COPY backend/pyproject.toml /app/backend/pyproject.toml
COPY backend/app /app/backend/app
COPY backend/tests /app/backend/tests
COPY backend/scripts /app/backend/scripts
COPY backend/alembic.ini /app/backend/alembic.ini
COPY backend/alembic /app/backend/alembic
COPY data /app/data

RUN pip install --no-cache-dir --upgrade pip \
    && pip install --no-cache-dir --no-build-isolation /app/backend

WORKDIR /app/backend

EXPOSE 8000

CMD ["uvicorn", "app.main:create_app", "--factory", "--host", "0.0.0.0", "--port", "8000"]
