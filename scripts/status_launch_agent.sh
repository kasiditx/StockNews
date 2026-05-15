#!/usr/bin/env bash
set -euo pipefail

LABEL="com.kasidit.stock-news-alert"
RUNTIME_DIR="$HOME/.stock-news-alert"

launchctl print "gui/$(id -u)/$LABEL" 2>/dev/null || {
  echo "$LABEL is not loaded"
  exit 0
}

echo
echo "Recent stdout log:"
tail -n 20 "$RUNTIME_DIR/logs/stock-news.out.log" 2>/dev/null || true

echo
echo "Recent stderr log:"
tail -n 20 "$RUNTIME_DIR/logs/stock-news.err.log" 2>/dev/null || true
