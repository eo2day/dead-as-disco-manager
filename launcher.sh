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

echo "Installing/updating dependencies..."
.venv/bin/python -m pip install -r requirements.txt

echo "Launching Dead as Disco Music Manager..."
exec .venv/bin/python main.py
