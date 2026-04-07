#!/bin/bash
set -euo pipefail

PROJECT_ROOT="${1:-$(pwd)}"
PROJECT_ROOT="$(cd "$PROJECT_ROOT" && pwd)"
KEEP_RECENT="${PIPELINE_SMOKE_KEEP_RECENT:-3}"
DRY_RUN="${PIPELINE_SMOKE_CLEANUP_DRY_RUN:-0}"
SMOKE_ROOT="$PROJECT_ROOT/.pipeline"

if ! [[ "$KEEP_RECENT" =~ ^[0-9]+$ ]]; then
    echo "PIPELINE_SMOKE_KEEP_RECENT must be a non-negative integer" >&2
    exit 1
fi

mapfile -t SMOKE_DIRS < <(
    find "$SMOKE_ROOT" -maxdepth 1 -mindepth 1 -type d -name 'live-arb-smoke-*' -printf '%T@ %p\n' \
        | sort -nr \
        | awk '{print $2}'
)

if [ "${#SMOKE_DIRS[@]}" -eq 0 ]; then
    echo "No live-arb-smoke directories found under $SMOKE_ROOT"
    exit 0
fi

echo "Smoke root: $SMOKE_ROOT"
echo "Found: ${#SMOKE_DIRS[@]}"
echo "Keep recent: $KEEP_RECENT"
echo "Dry run: $DRY_RUN"
echo

if [ "${#SMOKE_DIRS[@]}" -le "$KEEP_RECENT" ]; then
    echo "Nothing to clean."
    exit 0
fi

for ((idx=0; idx<${#SMOKE_DIRS[@]}; idx++)); do
    dir="${SMOKE_DIRS[$idx]}"
    if [ "$idx" -lt "$KEEP_RECENT" ]; then
        echo "KEEP  $dir"
        continue
    fi

    if [ "$DRY_RUN" = "1" ]; then
        echo "DELETE $dir"
        continue
    fi

    rm -rf -- "$dir"
    echo "DELETE $dir"
done
