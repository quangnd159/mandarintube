#!/bin/sh
# Refresh the catalog and rebuild the site. Pass "deploy" to publish the result.
set -eu
cd "$(dirname "$0")"

python3 pipeline/catalog.py --force
python3 pipeline/signals.py
python3 pipeline/mentions.py
python3 pipeline/disclosure.py flagged
python3 pipeline/build.py
# Check every listed video for YouTube's AI label and speech language, then rebuild without
# the ones that fail. Removing them lets new videos in, so check and rebuild a second time.
python3 pipeline/disclosure.py site
python3 pipeline/build.py
python3 pipeline/disclosure.py site
python3 pipeline/build.py

if [ "${1:-}" = "deploy" ]; then
  npx --yes wrangler@4.45.0 deploy
fi
