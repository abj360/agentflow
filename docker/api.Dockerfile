FROM python:3.12-slim

WORKDIR /app

COPY pyproject.toml ./
COPY packages ./packages
COPY apps/api ./apps/api

RUN pip install --no-cache-dir -e ".[dev]" && pip install --no-cache-dir -e packages/core

ENV PYTHONUNBUFFERED=1

RUN useradd --create-home agentflow
USER agentflow

CMD ["uvicorn", "apps.api.main:app", "--host", "0.0.0.0", "--port", "8000"]
