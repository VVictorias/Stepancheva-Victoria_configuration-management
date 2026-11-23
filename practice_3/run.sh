#!/usr/bin/env bash
set -eu

dir="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
case "${1:-}" in
    assemble)
        shift
        exec python3 -B "$dir/src/assembler.py" "$@"
        ;;
    interpret)
        shift
        exec python3 -B "$dir/src/interpreter.py" "$@"
        ;;
    *)
        echo "Использование: bash run.sh {assemble|interpret} --help" >&2
        exit 2
        ;;
esac
