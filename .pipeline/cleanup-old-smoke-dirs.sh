#!/bin/bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="${1:-$(pwd)}"
PROJECT_ROOT="$(cd "$PROJECT_ROOT" && pwd)"
KEEP_RECENT="${PIPELINE_SMOKE_KEEP_RECENT:-3}"
DRY_RUN="${PIPELINE_SMOKE_CLEANUP_DRY_RUN:-0}"
SMOKE_ROOT="$PROJECT_ROOT/.pipeline"
PATTERN="${PIPELINE_SMOKE_PATTERN:-live-arb-smoke-*}"

if ! [[ "$KEEP_RECENT" =~ ^[0-9]+$ ]]; then
    echo "PIPELINE_SMOKE_KEEP_RECENT must be a non-negative integer" >&2
    exit 1
fi

# shellcheck disable=SC1090
. "$SCRIPT_DIR/smoke-cleanup-lib.sh"

mapfile -t SMOKE_DIRS < <(_smoke_enumerate_dirs "$SMOKE_ROOT" "$PATTERN")

if [ "${#SMOKE_DIRS[@]}" -eq 0 ]; then
    echo "No $PATTERN directories found under $SMOKE_ROOT"
    exit 0
fi

echo "Smoke root: $SMOKE_ROOT"
echo "Pattern: $PATTERN"
echo "Found: ${#SMOKE_DIRS[@]}"
echo "Keep recent: $KEEP_RECENT"
echo "Dry run: $DRY_RUN"
echo

if [ "${#SMOKE_DIRS[@]}" -le "$KEEP_RECENT" ]; then
    echo "Nothing to clean."
    exit 0
fi

# Manual cleanup always passes protect_tracked=1 so that a pattern override
# (for example PIPELINE_SMOKE_PATTERN='live-blocked-smoke-*') cannot delete
# checked-in fixture directories. Auto-prune callers in the smoke helpers
# keep picking protect_tracked themselves for their own pattern.
prune_smoke_dirs "$SMOKE_ROOT" "$PATTERN" "$KEEP_RECENT" 1 "$DRY_RUN"
