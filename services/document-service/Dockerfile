# syntax=docker/dockerfile:1
FROM python:3.12-slim-bookworm AS builder

RUN apt-get update \
    && apt-get install -y --no-install-recommends build-essential libpq-dev \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /build

RUN python -m venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

COPY libs/py-common /build/libs/py-common
COPY services/document-service/requirements.txt /build/requirements.txt

RUN pip install --no-cache-dir --upgrade pip \
    && pip install --no-cache-dir -r requirements.txt \
    && pip install --no-cache-dir /build/libs/py-common

FROM python:3.12-slim-bookworm AS runtime

RUN apt-get update \
    && apt-get install -y --no-install-recommends libpq5 \
    && rm -rf /var/lib/apt/lists/* \
    && useradd --create-home --uid 1000 --shell /bin/bash app

WORKDIR /app

COPY --from=builder /opt/venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

COPY services/document-service /app

RUN chmod +x /app/docker-entrypoint.sh

USER app

ENV PYTHONUNBUFFERED=1
ENV DJANGO_SETTINGS_MODULE=document_service.settings

EXPOSE 8010

ENTRYPOINT ["/app/docker-entrypoint.sh"]
CMD ["gunicorn", "--bind", "0.0.0.0:8010", "--workers", "2", "document_service.wsgi:application"]
