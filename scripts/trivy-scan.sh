#!/usr/bin/env bash
# Локальный запуск Trivy через Docker, чтобы не ставить его в систему.
#
#   ./scripts/trivy-scan.sh tama-backend:fat
#   SEVERITY=CRITICAL ./scripts/trivy-scan.sh tama-backend:good

set -euo pipefail

IMAGE="${1:?Укажи образ: ./scripts/trivy-scan.sh my-image:tag}"
SEVERITY="${SEVERITY:-CRITICAL,HIGH}"

# Кеш базы уязвимостей в томе, иначе Trivy качает её заново
# при каждом запуске (это как раз те самые полторы минуты ожидания).
docker run --rm \
  -v /var/run/docker.sock:/var/run/docker.sock \
  -v trivy-cache:/root/.cache/trivy \
  aquasec/trivy:0.57.1 image \
  --scanners vuln \
  --severity "$SEVERITY" \
  --format table \
  "$IMAGE"
