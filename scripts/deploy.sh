#!/usr/bin/env bash
# Деплой конкретного тега через docker-compose.ci.yml.
# Запоминает текущий и предыдущий тег, чтобы потом можно было откатиться.
#
#   ./scripts/deploy.sh sha-610143c

set -euo pipefail

TAG="${1:?Укажи тег: ./scripts/deploy.sh sha-610143c}"
STATE_DIR=".deploy"
mkdir -p "$STATE_DIR"

# Сдвигаем историю: текущий становится предыдущим
if [ -f "$STATE_DIR/current_tag" ]; then
  cp "$STATE_DIR/current_tag" "$STATE_DIR/previous_tag"
fi
echo "$TAG" > "$STATE_DIR/current_tag"

export BACKEND_IMAGE="${BACKEND_IMAGE:-ghcr.io/ngdis13/tamagotchi-backend}"
export IMAGE_TAG="$TAG"

docker compose -f docker-compose.ci.yml up -d --pull missing

API_URL="${API_URL:-http://localhost:${BACKEND_PORT:-8000}/api/pets}"

# Ждём, пока сервис начнёт отвечать
for _ in $(seq 1 15); do
  if curl -fsS "$API_URL" >/dev/null 2>&1; then
    echo "Задеплоен $TAG, сервис отвечает"
    exit 0
  fi
  sleep 2
done

echo "Тег $TAG не поднялся"
docker compose -f docker-compose.ci.yml logs --tail=50
exit 1
