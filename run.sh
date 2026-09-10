#!/usr/bin/env sh
# No-install launcher for ORBITFALL.
# Prefers a local .venv (from `uv sync` or `python -m venv .venv`); otherwise
# falls back to the active python3. pygame-ce must be importable in whichever
# interpreter is used (see README).
set -eu
cd "$(dirname "$0")"
PYTHON=python3
if [ -x .venv/bin/python ]; then
    PYTHON=.venv/bin/python
fi
exec "$PYTHON" -m game.main "$@"
