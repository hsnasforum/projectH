#!/bin/bash
set -euo pipefail

PIPELINE_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ARCHIVE_ROOT="$PIPELINE_DIR/archive"
DRY_RUN="${PIPELINE_ARCHIVE_DRY_RUN:-0}"

CONTROL_FILES=(
    "claude_handoff.md"
    "gemini_request.md"
    "gemini_advice.md"
    "operator_request.md"
    "session_arbitration_draft.md"
)

usage() {
    cat <<'EOF'
Usage:
  .pipeline/archive-stale-control-slots.sh --all-stale
  .pipeline/archive-stale-control-slots.sh <slot-basename> [<slot-basename> ...]

Notes:
  - Only known .pipeline control-slot basenames are accepted.
  - The newest existing control slot is never archived.
  - Archived files move to .pipeline/archive/YYYY-MM-DD/
  - Set PIPELINE_ARCHIVE_DRY_RUN=1 for a no-op preview.
EOF
}

is_known_slot() {
    local name="$1"
    local item
    for item in "${CONTROL_FILES[@]}"; do
        if [ "$item" = "$name" ]; then
            return 0
        fi
    done
    return 1
}

newest_slot_name() {
    local newest_name=""
    local newest_epoch="-1"
    local item path epoch

    for item in "${CONTROL_FILES[@]}"; do
        path="$PIPELINE_DIR/$item"
        if [ ! -f "$path" ]; then
            continue
        fi
        epoch="$(stat -c '%Y' "$path")"
        if [ "$epoch" -gt "$newest_epoch" ]; then
            newest_epoch="$epoch"
            newest_name="$item"
        fi
    done

    printf '%s' "$newest_name"
}

archive_slot() {
    local name="$1"
    local newest="$2"
    local path="$PIPELINE_DIR/$name"
    local archive_day archive_stamp target base counter

    if [ ! -f "$path" ]; then
        echo "SKIP missing $name"
        return 0
    fi

    if [ "$name" = "$newest" ]; then
        echo "SKIP newest control file $name"
        return 0
    fi

    archive_day="$(date '+%F')"
    archive_stamp="$(date -d "@$(stat -c '%Y' "$path")" '+%Y%m%d-%H%M%S')"
    base="${name%.md}.${archive_stamp}"
    target="$ARCHIVE_ROOT/$archive_day/${base}.md"
    counter=1

    while [ -e "$target" ]; do
        target="$ARCHIVE_ROOT/$archive_day/${base}-${counter}.md"
        counter=$((counter + 1))
    done

    if [ "$DRY_RUN" = "1" ]; then
        echo "ARCHIVE $path -> $target"
        return 0
    fi

    mkdir -p "$(dirname "$target")"
    mv -- "$path" "$target"
    echo "ARCHIVE $path -> $target"
}

main() {
    local newest targets=()
    local arg

    if [ "$#" -eq 0 ]; then
        usage >&2
        exit 1
    fi

    newest="$(newest_slot_name)"
    if [ -z "$newest" ]; then
        echo "No control slots found under $PIPELINE_DIR"
        exit 0
    fi

    if [ "$1" = "--all-stale" ]; then
        targets=("${CONTROL_FILES[@]}")
    else
        for arg in "$@"; do
            if [ "$arg" = "--help" ] || [ "$arg" = "-h" ]; then
                usage
                exit 0
            fi
            if ! is_known_slot "$arg"; then
                echo "Unknown control slot: $arg" >&2
                usage >&2
                exit 1
            fi
            targets+=("$arg")
        done
    fi

    echo "Pipeline dir: $PIPELINE_DIR"
    echo "Newest control file: $newest"
    echo "Dry run: $DRY_RUN"
    echo

    for arg in "${targets[@]}"; do
        archive_slot "$arg" "$newest"
    done
}

main "$@"
