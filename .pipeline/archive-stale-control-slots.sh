#!/bin/bash
set -euo pipefail

PIPELINE_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "$PIPELINE_DIR/.." && pwd)"
ARCHIVE_ROOT="$PIPELINE_DIR/archive"
DRY_RUN="${PIPELINE_ARCHIVE_DRY_RUN:-0}"
PYTHON_BIN="${PYTHON_BIN:-python3}"

CONTROL_FILES=(
    "implement_handoff.md"
    "advisory_request.md"
    "advisory_advice.md"
    "operator_request.md"
    "session_arbitration_draft.md"
    "claude_handoff.md"
    "gemini_request.md"
    "gemini_advice.md"
)

usage() {
    cat <<'EOF'
Usage:
  .pipeline/archive-stale-control-slots.sh --all-stale
  .pipeline/archive-stale-control-slots.sh <slot-basename> [<slot-basename> ...]

Notes:
  - Only known .pipeline control-slot basenames are accepted.
  - Role-based canonical names are preferred; historical aliases are accepted
    only so old files can be archived safely during migration.
  - The active control slot by CONTROL_SEQ/status ordering is never archived.
    If no valid active control can be resolved, the newest file by mtime is kept
    as a conservative fallback.
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
    local protected="$2"
    local protected_status="$3"
    local protected_seq="$4"
    local path="$PIPELINE_DIR/$name"
    local archive_day archive_stamp target base counter file_sha

    if [ ! -f "$path" ]; then
        echo "SKIP missing $name"
        return 0
    fi

    if [ "$name" = "$protected" ]; then
        echo "SKIP protected control file $name"
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

    file_sha="$(sha256sum "$path" | awk '{print $1}')"
    mkdir -p "$(dirname "$target")"
    mv -- "$path" "$target"
    write_archive_manifest "$name" "$path" "$target" "$file_sha" "$protected" "$protected_status" "$protected_seq"
    echo "ARCHIVE $path -> $target"
}

write_archive_manifest() {
    local name="$1"
    local source_path="$2"
    local target_path="$3"
    local file_sha="$4"
    local protected="$5"
    local protected_status="$6"
    local protected_seq="$7"
    local manifest_path="$ARCHIVE_ROOT/$(date '+%F')/archive-manifest.jsonl"

    PYTHONPATH="$REPO_ROOT${PYTHONPATH:+:$PYTHONPATH}" "$PYTHON_BIN" - "$manifest_path" "$REPO_ROOT" "$PIPELINE_DIR" "$name" "$source_path" "$target_path" "$file_sha" "$protected" "$protected_status" "$protected_seq" <<'PY'
import json
import sys
from pathlib import Path

from pipeline_runtime.schema import (
    control_slot_spec_for_filename,
    iso_utc,
    parse_control_slots,
    read_control_meta,
)


def repo_relative(path: Path, repo_root: Path) -> str:
    try:
        return str(path.resolve().relative_to(repo_root.resolve()))
    except ValueError:
        return str(path)


def control_seq(value: str) -> int | None:
    return int(value) if str(value).isdigit() else None

manifest_path = Path(sys.argv[1])
repo_root = Path(sys.argv[2])
pipeline_dir = Path(sys.argv[3])
name = sys.argv[4]
source_path = Path(sys.argv[5])
target_path = Path(sys.argv[6])
target_meta = read_control_meta(target_path)
target_spec = control_slot_spec_for_filename(name)
pre_active_control = {
    "file": sys.argv[8],
    "status": sys.argv[9],
    "control_seq": control_seq(sys.argv[10]),
}
entry = {
    "at": iso_utc(),
    "action": "archive_control_slot",
    "dry_run": False,
    "slot": name,
    "source_path": repo_relative(source_path, repo_root),
    "target_path": repo_relative(target_path, repo_root),
    "sha256": sys.argv[7],
    "archived_slot": {
        "file": name,
        "status": str(target_meta.get("status") or ""),
        "control_seq": target_meta.get("control_seq"),
        "slot_id": target_spec.slot_id if target_spec else "",
        "canonical_file": target_spec.canonical_filename if target_spec else "",
        "is_legacy_alias": bool(target_spec and name != target_spec.canonical_filename),
    },
    "pre_active_control": pre_active_control,
    "protected_control": pre_active_control,
    "post_active_control": (parse_control_slots(pipeline_dir).get("active") or {}),
}
manifest_path.parent.mkdir(parents=True, exist_ok=True)
with manifest_path.open("a", encoding="utf-8") as fh:
    fh.write(json.dumps(entry, ensure_ascii=False, sort_keys=True) + "\n")
PY
}

active_slot_metadata() {
    PYTHONPATH="$REPO_ROOT${PYTHONPATH:+:$PYTHONPATH}" "$PYTHON_BIN" -c '
import sys
from pathlib import Path
from pipeline_runtime.schema import parse_control_slots

active = (parse_control_slots(Path(sys.argv[1])).get("active") or {})
print(active.get("file", ""))
print(active.get("status", ""))
seq = active.get("control_seq")
print("" if seq is None else seq)
' "$PIPELINE_DIR"
}

main() {
    local protected targets=()
    local protected_status=""
    local protected_seq=""
    local active_metadata_text arg

    if [ "$#" -eq 0 ]; then
        usage >&2
        exit 1
    fi

    active_metadata_text="$(active_slot_metadata)" || {
        echo "ERROR failed to resolve active control slot with pipeline_runtime.schema" >&2
        exit 1
    }
    mapfile -t active_metadata <<< "$active_metadata_text"
    protected="${active_metadata[0]:-}"
    protected_status="${active_metadata[1]:-}"
    protected_seq="${active_metadata[2]:-}"
    if [ -z "$protected" ]; then
        protected="$(newest_slot_name)"
    fi
    if [ -z "$protected" ]; then
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
    echo "Protected control file: $protected"
    echo "Dry run: $DRY_RUN"
    echo

    for arg in "${targets[@]}"; do
        archive_slot "$arg" "$protected" "$protected_status" "$protected_seq"
    done
}

main "$@"
