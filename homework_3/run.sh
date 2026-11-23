#!/usr/bin/env bash
set -eu

dir="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
exec python3 -B "$dir/src/main.py" "$@"
