#!/usr/bin/env bash
set -euo pipefail

if [[ $# -ne 1 ]]; then
  echo "用法：$0 /srv/pdp-lab/releases/<commit>" >&2
  exit 1
fi

RELEASE_DIR=$(cd "$1" && pwd)
ENV_FILE=${PDP_ENV_FILE:-/srv/pdp-lab/shared/.env.production}

if [[ ! -f "$RELEASE_DIR/compose.production.yml" || ! -f "$ENV_FILE" ]]; then
  echo "恢复版本或生产环境文件不存在。" >&2
  exit 1
fi

PDP_ENV_FILE="$ENV_FILE" "$RELEASE_DIR/deploy/deploy.sh"
ln -sfn "$RELEASE_DIR" /srv/pdp-lab/current
echo "已恢复到：$RELEASE_DIR"
