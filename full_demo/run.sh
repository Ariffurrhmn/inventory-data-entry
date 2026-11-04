#!/usr/bin/env bash
# Linux/macOS launcher:  ./full_demo/run.sh [--lan] [--policy strict|demo_reconcile] [--port N] [--extractor-cmd CMD]
set -euo pipefail
here="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
py="${PYTHON:-python3}"
command -v tesseract >/dev/null || { echo "Install Tesseract first (Debian/Ubuntu: sudo apt install tesseract-ocr; macOS: brew install tesseract)."; exit 1; }
"$py" -c "import sklearn, PIL, joblib, numpy, scipy" 2>/dev/null || { echo "Installing Python packages..."; "$py" -m pip install -r "$here/requirements.txt"; }
tess="$here/../classifier/engine/.cache/tessdata"
if [ ! -f "$tess/eng.traineddata" ]; then
  src="$(find /usr/share /opt/homebrew/share /usr/local/share -name eng.traineddata 2>/dev/null | head -n1 || true)"
  [ -n "$src" ] || { echo "Could not find eng.traineddata; copy it to $tess/"; exit 1; }
  mkdir -p "$tess" && cp "$src" "$tess/" && echo "Copied Tesseract English data to $tess"
fi
exec "$py" -u "$here/server.py" "$@"
