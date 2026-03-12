FROM python:3.12-slim AS base

WORKDIR /app

COPY pyproject.toml .
COPY importer/ importer/
COPY urls/ urls/
COPY recipes/ recipes/

RUN pip install --no-cache-dir .

# ── dev stage: adds test deps + test files, used by CI ───────────────────────
FROM base AS dev

COPY tests/ tests/
RUN pip install --no-cache-dir ".[dev]"

CMD ["pytest", "--cov=importer", "--cov-report=term-missing"]

# ── prod stage: default, no test code ────────────────────────────────────────
FROM base AS prod

CMD ["python", "-m", "importer"]
