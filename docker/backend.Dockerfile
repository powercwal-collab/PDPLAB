FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1

WORKDIR /app

RUN groupadd --gid 10001 pdplab \
    && useradd --uid 10001 --gid pdplab --create-home pdplab

COPY requirements.txt /app/requirements.txt
RUN apt-get update \
    && apt-get install -y --no-install-recommends build-essential \
    && pip install --upgrade pip \
    && pip install -r /app/requirements.txt \
    && apt-get purge -y --auto-remove build-essential \
    && rm -rf /var/lib/apt/lists/*

COPY backend /app/backend
COPY deploy/backend-entrypoint.sh /app/deploy/backend-entrypoint.sh

RUN mkdir -p /app/backend/staticfiles /app/backend/media \
    && chown -R pdplab:pdplab /app

USER pdplab
WORKDIR /app/backend

EXPOSE 8000
ENTRYPOINT ["/app/deploy/backend-entrypoint.sh"]
CMD ["web"]
