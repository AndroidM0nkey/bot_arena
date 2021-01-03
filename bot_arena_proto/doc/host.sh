#!/bin/bash
set -e

function die {
    echo "$@"
    exit 1
}

cd bot_arena_proto || die "You have to run ./build.sh first"
python -m http.server "${1:-8000}"
