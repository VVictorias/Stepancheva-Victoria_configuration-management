#!/bin/sh
# Передать аргументы без изменения, независимо от текущего каталога.
set -eu
SCRIPT_DIR=$(CDPATH='' cd -- "$(dirname -- "$0")" && pwd)
exec python3 "$SCRIPT_DIR/src/cli.py" "$@"
