#!/usr/bin/env bash
# Thin wrapper: all logic lives in install.py (portable across Linux/macOS/WSL).
exec python3 "$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)/install.py" "$@"
