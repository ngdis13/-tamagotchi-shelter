#!/usr/bin/env bash
# Откат на предыдущий рабочий тег одной командой.
# Заодно замеряет, сколько времени откат занял.

set -euo pipefail

STATE_DIR=".deploy"
PREV_FILE="$STATE_DIR/previous_tag"

if [ ! -f "$PREV_FILE" ]; then
  echo "Нет файла $PREV_FILE — сначала сделай хотя бы один деплой"
  exit 1
fi

PREV_TAG="$(cat "$PREV_FILE")"
echo "Откатываюсь на $PREV_TAG"

START=$(date +%s)
./scripts/deploy.sh "$PREV_TAG"
END=$(date +%s)

echo "Откат занял $((END - START)) секунд"
