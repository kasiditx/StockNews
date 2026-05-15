#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
LABEL="com.kasidit.stock-news-alert"
PLIST_PATH="$HOME/Library/LaunchAgents/$LABEL.plist"
RUNTIME_DIR="$HOME/.stock-news-alert"
LOG_DIR="$RUNTIME_DIR/logs"

mkdir -p "$HOME/Library/LaunchAgents" "$LOG_DIR"

rsync -a --delete \
  --exclude ".git/" \
  --exclude ".venv/" \
  --exclude ".pytest_cache/" \
  --exclude ".ruff_cache/" \
  --exclude ".serena/" \
  --exclude "__pycache__/" \
  --exclude "logs/" \
  "$ROOT_DIR/" "$RUNTIME_DIR/"

if [[ ! -x "$RUNTIME_DIR/.venv/bin/python" ]]; then
  python3 -m venv "$RUNTIME_DIR/.venv"
fi

"$RUNTIME_DIR/.venv/bin/python" -m pip install -e "$RUNTIME_DIR" >/dev/null

cat > "$PLIST_PATH" <<PLIST
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
  <key>Label</key>
  <string>$LABEL</string>
  <key>ProgramArguments</key>
  <array>
    <string>/bin/bash</string>
    <string>$RUNTIME_DIR/scripts/watch.sh</string>
  </array>
  <key>WorkingDirectory</key>
  <string>$RUNTIME_DIR</string>
  <key>RunAtLoad</key>
  <true/>
  <key>KeepAlive</key>
  <true/>
  <key>StandardOutPath</key>
  <string>$LOG_DIR/stock-news.out.log</string>
  <key>StandardErrorPath</key>
  <string>$LOG_DIR/stock-news.err.log</string>
</dict>
</plist>
PLIST

launchctl bootout "gui/$(id -u)" "$PLIST_PATH" >/dev/null 2>&1 || true
launchctl bootstrap "gui/$(id -u)" "$PLIST_PATH"
launchctl enable "gui/$(id -u)/$LABEL"
launchctl kickstart -k "gui/$(id -u)/$LABEL"

echo "Installed and started $LABEL"
echo "Logs:"
echo "  $LOG_DIR/stock-news.out.log"
echo "  $LOG_DIR/stock-news.err.log"
