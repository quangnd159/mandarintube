#!/bin/sh
# Refresh the catalog by hand. The schedule runs the same job: see pipeline/update.py.
#   ./refresh.sh            new videos and posts, checks, titles, rebuild. Doesn't publish.
#   ./refresh.sh deploy     the same, then publish if the safety check passes
#   ./refresh.sh discover   find new candidate channels and write the review report
#   ./refresh.sh accept     publish a run the safety check stopped, after looking at it
#   ./refresh.sh status     when each job last ran
set -eu
cd "$(dirname "$0")"

case "${1:-}" in
  "") exec python3 pipeline/update.py run ;;
  deploy) exec python3 pipeline/update.py run --deploy ;;
  discover | accept | status) exec python3 pipeline/update.py "$1" ;;
  *) sed -n '2,7p' "$0"; exit 64 ;;
esac
