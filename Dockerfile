FROM python:3.12-slim AS builder

COPY --from=ghcr.io/astral-sh/uv:latest /uv /usr/local/bin/uv

WORKDIR /app
COPY pyproject.toml uv.lock ./
RUN uv sync --frozen --no-dev --no-install-project

FROM python:3.12-slim

RUN groupadd --system app && useradd --system --gid app --create-home app
WORKDIR /app

COPY --from=builder /app/.venv /app/.venv
COPY --chown=app:app app/ ./app/
COPY --chown=app:app alembic.ini ./alembic.ini
COPY --chown=app:app alembic/ ./alembic/
COPY --chown=app:app scripts/ ./scripts/

ENV PATH="/app/.venv/bin:$PATH"

USER app
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]