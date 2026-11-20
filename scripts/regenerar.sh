#!/usr/bin/env bash
# Regenera los CSV de data/ ejecutando los extractores dentro del contenedor `api`
# de AyudasPilot. No contiene credenciales: el acceso SSH se configura fuera
# (variables AP_SSH_HOST y, opcionalmente, AP_SSH_KEY / AP_DIR).
#   AP_SSH_HOST=root@servidor ./scripts/regenerar.sh [convocatorias|concesiones|todo]
# En el propio servidor: AP_SSH_HOST=local (sin SSH).
set -euo pipefail
cd "$(dirname "$0")/.."
: "${AP_SSH_HOST:?Define AP_SSH_HOST (p. ej. usuario@host)}"
AP_DIR="${AP_DIR:-/opt/ayudaspilot}"
SSH_OPTS=()
[ -n "${AP_SSH_KEY:-}" ] && SSH_OPTS+=(-i "$AP_SSH_KEY")
QUE="${1:-todo}"

run() {  # $1 = script python
  if [ "$AP_SSH_HOST" = local ]; then
    (cd "$AP_DIR" && docker compose -f docker-compose.prod.yml exec -T api python -) < "scripts/$1" \
      | python3 scripts/escribir_salida.py data
  else
    ssh "${SSH_OPTS[@]}" "$AP_SSH_HOST" \
      "cd $AP_DIR && docker compose -f docker-compose.prod.yml exec -T api python -" < "scripts/$1" \
      | python3 scripts/escribir_salida.py data
  fi
}
[[ "$QUE" == convocatorias || "$QUE" == todo ]] && run extraer_convocatorias.py
[[ "$QUE" == concesiones   || "$QUE" == todo ]] && run extraer_concesiones.py
python3 scripts/validar.py && python3 scripts/generar_datapackage.py
