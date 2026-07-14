#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR=$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)
ENV_FILE=${PDP_ENV_FILE:-$ROOT_DIR/.env.production}

if [[ ! -f "$ENV_FILE" ]]; then
  echo "缺少生产环境文件：$ENV_FILE" >&2
  exit 1
fi

export PDP_ENV_FILE="$ENV_FILE"
COMPOSE=(docker compose -p pdp-lab --env-file "$ENV_FILE" -f "$ROOT_DIR/compose.production.yml")
if grep -Eq '^PDP_ENABLE_LOCAL_INFRA=(1|true|yes)$' "$ENV_FILE"; then
  COMPOSE+=(--profile local-infra)
fi
if grep -Eq '^PDP_ENABLE_TLS=(1|true|yes)$' "$ENV_FILE"; then
  COMPOSE+=(-f "$ROOT_DIR/compose.tls.yml")
fi

"${COMPOSE[@]}" config --quiet
"${COMPOSE[@]}" build --pull
"${COMPOSE[@]}" up -d --remove-orphans

for attempt in {1..30}; do
  if curl --fail --silent --show-error http://127.0.0.1/healthz >/dev/null; then
    echo "PDP Lab 已通过生产健康检查。"
    "${COMPOSE[@]}" ps
    exit 0
  fi
  sleep 4
done

"${COMPOSE[@]}" ps
"${COMPOSE[@]}" logs --tail=120 web worker nginx
echo "部署后健康检查失败。" >&2
exit 1
