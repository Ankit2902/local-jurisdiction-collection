#!/usr/bin/env sh
set -eu
TASK_ROOT=$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)
cd "$TASK_ROOT"
if [ -z "${PYTHON:-}" ]; then
  if [ -x "$TASK_ROOT/.venv/bin/python" ]; then PYTHON="$TASK_ROOT/.venv/bin/python"; else PYTHON=python3; fi
fi
export PYTHON
export PYTHONDONTWRITEBYTECODE=1
case "${1:---offline}" in
  --offline) "$PYTHON" scripts/offline_replay.py ;;
  --target) "$PYTHON" scripts/collect_http.py --target "$2" ;;
  --native) "$PYTHON" scripts/native_samples.py ;;
  *) printf '%s\n' 'Usage: ./run.sh [--offline | --target jurisdiction-slug | --native]' >&2; exit 2 ;;
esac
