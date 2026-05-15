#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
PYTHON_BIN="$ROOT_DIR/.venv/bin/python"
WATCHLIST_PATH="$ROOT_DIR/config/watchlist.json"

if [[ ! -x "$PYTHON_BIN" ]]; then
  echo "Missing virtualenv. Run: python3 -m venv .venv && source .venv/bin/activate && pip install -e \".[dev]\"" >&2
  exit 1
fi

cd "$ROOT_DIR"

COMMAND=("$PYTHON_BIN" -m stock_alerts run-once)

if [[ -f "$WATCHLIST_PATH" && "$*" != *"--watchlist"* && "$*" != *"-h"* && "$*" != *"--help"* ]]; then
  COMMAND+=(--watchlist "$WATCHLIST_PATH")
fi

exec "${COMMAND[@]}" "$@"
