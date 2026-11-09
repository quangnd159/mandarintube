#!/bin/sh
# Turn the scheduled update on or off.
#   deploy/install-schedule.sh          install it for this user
#   deploy/install-schedule.sh remove   take it out again
#
# launchd checks daily and whenever a drive is mounted, and update.py works out what's due.
# So a run missed because the Mac was asleep or the drive was unplugged happens at the next
# chance. While the drive is unplugged the job simply can't start.
set -eu

LABEL=com.dqnotes.mandarintube.update
PLIST="$HOME/Library/LaunchAgents/$LABEL.plist"
DOMAIN="gui/$(id -u)"

if [ "${1:-}" = "remove" ]; then
  launchctl bootout "$DOMAIN/$LABEL" 2>/dev/null || true
  rm -f "$PLIST"
  echo "Schedule removed."
  exit 0
fi

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
PYTHON="$(command -v python3)"
for tool in yt-dlp npx claude; do
  command -v "$tool" >/dev/null || { echo "$tool isn't on PATH"; exit 1; }
done
# launchd starts with a bare PATH, so give it the folders these tools live in.
TOOL_PATH="$(for tool in python3 yt-dlp npx claude git; do dirname "$(command -v "$tool")"; done | awk '!seen[$0]++' | paste -sd : -):/usr/bin:/bin"

mkdir -p "$HOME/Library/LaunchAgents" "$HOME/Library/Logs"
cat > "$PLIST" <<EOF
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
  <key>Label</key><string>$LABEL</string>
  <key>ProgramArguments</key>
  <array>
    <string>/usr/bin/caffeinate</string>
    <string>-i</string>
    <string>$PYTHON</string>
    <string>$ROOT/pipeline/update.py</string>
    <string>tick</string>
  </array>
  <key>EnvironmentVariables</key>
  <dict><key>PATH</key><string>$TOOL_PATH</string></dict>
  <key>StartCalendarInterval</key>
  <dict><key>Hour</key><integer>10</integer><key>Minute</key><integer>0</integer></dict>
  <key>StartOnMount</key><true/>
  <key>ProcessType</key><string>Background</string>
  <key>StandardOutPath</key><string>$HOME/Library/Logs/mandarintube-update.log</string>
  <key>StandardErrorPath</key><string>$HOME/Library/Logs/mandarintube-update.log</string>
</dict>
</plist>
EOF

plutil -lint "$PLIST"
launchctl bootout "$DOMAIN/$LABEL" 2>/dev/null || true
launchctl bootstrap "$DOMAIN" "$PLIST"
echo "Schedule installed. It checks daily at 10:00 and when a drive is mounted."
echo "Try it now: launchctl kickstart $DOMAIN/$LABEL"
