#!/usr/bin/env sh
set -eu

ROOT="$(CDPATH= cd -- "$(dirname "$0")/.." && pwd)"
cd "$ROOT"

PYTHON=python3
RUFF=
PYTEST=

if [ -x backend/.venv/bin/python ]; then
  PYTHON="$ROOT/backend/.venv/bin/python"
  RUFF="$ROOT/backend/.venv/bin/ruff"
  PYTEST="$ROOT/backend/.venv/bin/pytest"
elif command -v ruff >/dev/null 2>&1 && command -v pytest >/dev/null 2>&1; then
  RUFF=ruff
  PYTEST=pytest
fi

"$PYTHON" -m compileall -q backend/app backend/tests
node --check extension/background.js
node --check extension/popup.js
node --check extension/options.js
node --check extension/content.js
python3 -m json.tool extension/manifest.json >/dev/null

if [ -n "$RUFF" ]; then
  "$RUFF" check backend
  "$RUFF" format --check backend
fi

if [ -n "$PYTEST" ]; then
  (cd backend && "$PYTEST")
fi

if [ -d extension/node_modules ]; then
  (cd extension && npm run lint && npm run format:check && npm test)
fi

echo "VisionX checks completed."
