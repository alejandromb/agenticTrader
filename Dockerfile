FROM python:3.12-slim AS builder

ENV PIP_DISABLE_PIP_VERSION_CHECK=1 \
    PIP_NO_CACHE_DIR=1

WORKDIR /build

COPY pyproject.toml Agentic_Trading_Project_Summary.md ./
COPY src ./src
COPY alembic.ini ./
COPY migrations ./migrations
COPY schemas ./schemas

RUN python -m pip install --upgrade pip build \
    && python -m build --wheel --outdir /wheels


FROM python:3.12-slim AS runtime

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1 \
    PIP_NO_CACHE_DIR=1

RUN groupadd --system agentic \
    && useradd --system --gid agentic --create-home agentic

WORKDIR /app

COPY --from=builder /wheels /wheels
RUN python -m pip install --upgrade 'pip>=26.2.1' \
    && python -m pip install /wheels/*.whl \
    && rm -rf /wheels

COPY alembic.ini ./
COPY migrations ./migrations
COPY schemas ./schemas

RUN mkdir -p /app/data /app/artifacts \
    && chown -R agentic:agentic /app

USER agentic

ENTRYPOINT ["agentic-trading"]
CMD ["--help"]


FROM runtime AS development

USER root
COPY --from=builder /build /build
RUN python -m pip install --no-cache-dir '/build[dev]'

COPY tests ./tests
COPY examples ./examples

RUN chown -R agentic:agentic /app /build
USER agentic

ENTRYPOINT []
CMD ["pytest"]
