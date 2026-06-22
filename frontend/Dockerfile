FROM python:3.11-slim

WORKDIR /app

COPY dist /app/dist

EXPOSE 4173

CMD ["python", "-m", "http.server", "4173", "--directory", "/app/dist", "--bind", "0.0.0.0"]
