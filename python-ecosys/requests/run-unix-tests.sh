#!/usr/bin/env bash
# Run requests package tests on MicroPython unix port (mock + live).
set -euo pipefail

MICROPYTHON="${MICROPYTHON:-../../../micropython/ports/unix/build-standard/micropython}"
ROOT="$(cd "$(dirname "$0")" && pwd)"

if [[ ! -x "$MICROPYTHON" ]]; then
  echo "Build unix port first:" >&2
  echo "  cd micropython/ports/unix && make submodules && make" >&2
  exit 1
fi

cd "$ROOT"
echo "== Mock tests (test_requests.py) =="
"$MICROPYTHON" test_requests.py

echo "== Live tests (test_requests_live.py) =="
"$MICROPYTHON" test_requests_live.py

echo "== All unix tests passed =="
