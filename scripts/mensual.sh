#!/usr/bin/env bash
# Regeneración mensual desatendida (cron del servidor, día 2 de cada mes).
# Extrae, valida y, solo si los datos cambian y la validación pasa, hace commit y push.
set -euo pipefail
cd "$(dirname "$0")/.."
git pull -q --ff-only
AP_SSH_HOST=local ./scripts/regenerar.sh todo
git add -A data datapackage.json
if git diff --cached --quiet; then
  echo "$(date -Is) sin cambios"
  exit 0
fi
git -c user.name="AyudasPilot" -c user.email="hola@ayudaspilot.com" \
  commit -q -m "Actualización mensual de los datos (corte $(date +%F))"
git push -q
echo "$(date -Is) publicado $(git rev-parse --short HEAD)"
