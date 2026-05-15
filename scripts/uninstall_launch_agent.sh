#!/usr/bin/env bash
set -euo pipefail

LABEL="com.kasidit.stock-news-alert"
PLIST_PATH="$HOME/Library/LaunchAgents/$LABEL.plist"

launchctl bootout "gui/$(id -u)" "$PLIST_PATH" >/dev/null 2>&1 || true
rm -f "$PLIST_PATH"

echo "Stopped and removed $LABEL"
echo "Runtime files are kept at $HOME/.stock-news-alert"
