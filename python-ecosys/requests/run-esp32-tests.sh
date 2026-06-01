#!/usr/bin/env bash
# Deploy requests package to ESP32 and run mock + live tests via mpremote.
set -euo pipefail

PORT="${PORT:-/dev/ttyACM0}"
MPREMOTE="${MPREMOTE:-pipx run mpremote}"
ROOT="$(cd "$(dirname "$0")" && pwd)"

run_mp() {
  $MPREMOTE connect "$PORT" "$@"
}

cd "$ROOT"
echo "== Deploy requests to :lib/requests =="
run_mp fs mkdir :lib 2>/dev/null || true
run_mp fs mkdir :lib/requests 2>/dev/null || true
run_mp fs cp requests/__init__.py :lib/requests/__init__.py
run_mp fs cp requests/_http.py :lib/requests/_http.py

echo "== Mock tests =="
run_mp run test_requests.py

echo "== Live tests =="
run_mp run test_requests_live.py

echo "== ESP32 tests passed =="
