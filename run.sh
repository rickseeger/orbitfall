#!/usr/bin/env sh
# No-install launcher for ORBITFALL.
# Requires pygame-ce to be importable in the active Python (see README).
set -eu
cd "$(dirname "$0")"
exec python3 -m game.main "$@"
