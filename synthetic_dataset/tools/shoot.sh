#!/bin/bash
# Batch-screenshot all generated HTML documents to PNG using headless Chrome.
set -e

CHROME="/c/Program Files/Google/Chrome/Application/chrome.exe"
BASE="E:/.shortcut-targets-by-id/1yOBXNuSORBcOSWDhEg-YF1MEWIDvc8J2/Capstone- Inventory Management System/synthetic_dataset"
PROFILE="/c/Users/WINDOW~1/AppData/Local/Temp/claude/chrome_shot_profile"
mkdir -p "$PROFILE" "$BASE/images"

count=0
total=$(ls "$BASE/html"/*.html | wc -l)

for f in "$BASE/html"/*.html; do
  name=$(basename "$f" .html)
  out="$BASE/images/${name}.png"

  # window size depends on doc type/production method (thermal = narrow, others = wide)
  case "$name" in
    receipt_*) size="480,900" ;;
    *) size="860,1000" ;;
  esac

  "$CHROME" --headless=new --disable-gpu --hide-scrollbars \
    --user-data-dir="$PROFILE" --window-size="$size" \
    --virtual-time-budget=2000 \
    --screenshot="$out" \
    "file:///$f" >/dev/null 2>&1

  count=$((count+1))
  if (( count % 20 == 0 )); then
    echo "  ...$count / $total"
  fi
done

echo "Done: $count screenshots written to $BASE/images"
