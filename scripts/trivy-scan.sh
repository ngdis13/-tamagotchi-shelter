#!/usr/bin/env bash
# Локальный запуск Trivy через Docker, чтобы не ставить его в систему.
#
#   ./scripts/trivy-scan.sh tama-backend:fat
#   SEVERITY=CRITICAL ./scripts/trivy-scan.sh tama-backend:good

set -euo pipefail

IMAGE="${1:?Укажи образ: ./scripts/trivy-scan.sh my-image:tag}"
SEVERITY="${SEVERITY:-CRITICAL,HIGH}"

docker run --rm \
  -v /var/run/docker.sock:/var/run/docker.sock \
  aquasec/trivy:0.57.1 image \
  --scanners vuln \
  --severity "$SEVERITY" \
  --format table \
  "$IMAGE"
