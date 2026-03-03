#!/usr/bin/env bash
set -euo pipefail

if [ "$#" -lt 1 ]; then
  echo "Usage: ./run.sh <source.fk>" >&2
  exit 1
fi

python -m freakc "$1"

