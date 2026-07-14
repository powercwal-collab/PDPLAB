FROM python:3.12-slim

ARG PIP_INDEX_URL=https://pypi.org/simple

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DEFAULT_TIMEOUT=120 \
    PIP_RETRIES=5 \
    PIP_INDEX_URL=${PIP_INDEX_URL}

WORKDIR /app

RUN groupadd --gid 10001 pdplab \
    && useradd --uid 10001 --gid pdplab --create-home pdplab

COPY requirements.txt /app/requirements.txt
RUN pip install --upgrade pip setuptools wheel \
    && pip install --no-build-isolation -r /app/requirements.txt

COPY backend /app/backend
COPY deploy/backend-entrypoint.sh /app/deploy/backend-entrypoint.sh

RUN mkdir -p /app/backend/staticfiles /app/backend/media \
    && chown -R pdplab:pdplab /app

USER pdplab
WORKDIR /app/backend

EXPOSE 8000
ENTRYPOINT ["/app/deploy/backend-entrypoint.sh"]
CMD ["web"]
