FROM python:3.13.7-slim AS base

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1

WORKDIR /app

RUN addgroup --system processos && adduser --system --ingroup processos processos

COPY pyproject.toml ./
COPY app ./app
RUN pip install --upgrade pip==25.2 && pip install .

USER processos
EXPOSE 8000
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]

FROM base AS development
USER root
RUN pip install ".[dev]"
USER processos
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000", "--reload"]

