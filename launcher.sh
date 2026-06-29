#!/usr/bin/env bash
set -euo pipefail

cd "$(dirname "$0")"

if command -v python3 >/dev/null 2>&1; then
  PYTHON=python3
elif command -v python >/dev/null 2>&1; then
  PYTHON=python
else
  echo "Python 3 was not found. Install Python, then try again."
  exit 1
fi

if [[ ! -x .venv/bin/python ]]; then
  echo "Creating virtual environment..."
  "$PYTHON" -m venv .venv
fi

REQ_HASH="$(
  .venv/bin/python - <<'PY'
import hashlib
from pathlib import Path
print(hashlib.sha256(Path("requirements.txt").read_bytes()).hexdigest())
PY
)"

STAMP_FILE=".venv/requirements.sha256"
STAMP_VALUE=""
if [[ -f "$STAMP_FILE" ]]; then
  STAMP_VALUE="$(<"$STAMP_FILE")"
fi

if [[ "$REQ_HASH" != "$STAMP_VALUE" ]]; then
  echo "Installing/updating dependencies..."
  .venv/bin/python -m pip install -r requirements.txt
  printf '%s\n' "$REQ_HASH" > "$STAMP_FILE"
else
  echo "Dependencies unchanged; skipping pip install."
fi

echo "Launching Dead as Disco Music Manager..."
exec .venv/bin/python main.py
