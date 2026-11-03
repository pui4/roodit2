FROM python:3.14-slim-trixie

RUN apt-get update \
    && apt-get install -y --no-install-recommends libmagic1 \
    && rm -rf /var/lib/apt/lists/*

COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/

COPY . /app
ENV UV_NO_DEV=1
WORKDIR /app
RUN uv sync --locked

ENV PATH="/app/.venv/bin:$PATH"

RUN useradd -r -m app \
    && mkdir -p /app/data \
    && chown -R app /app/data
USER app

VOLUME /app/data
CMD ["rooditpy"]