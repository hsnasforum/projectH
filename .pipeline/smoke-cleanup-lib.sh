# Shared helpers for pruning generated smoke workspace directories under
# `.pipeline/`. Source this from bash scripts with:
#
#   . "$SCRIPT_DIR/.pipeline/smoke-cleanup-lib.sh"
#   prune_smoke_dirs <smoke_root> <pattern> <keep_recent> [protect_tracked=0] [dry_run=0]
#
# Contract:
#   - Selects directories directly under <smoke_root> matching the literal
#     glob <pattern>, sorted newest-first by mtime.
#   - Keeps the newest <keep_recent> entries and deletes the rest.
#   - When <protect_tracked> is "1", any candidate directory whose path
#     contains git-tracked files (per `git ls-files --error-unmatch -- <dir>`)
#     is skipped instead of deleted. This is how blocked-smoke cleanup
#     avoids pruning checked-in `.pipeline/live-blocked-smoke-*` fixtures.
#   - When <protect_tracked> is "1" and <smoke_root> is not inside a git
#     work tree, the function fails closed: it prints an explicit diagnostic
#     to stderr and returns non-zero before enumerating or deleting anything.
#     That prevents `protect_tracked=1` from silently degrading to "no
#     protection" when tracked-file lookups cannot run.
#   - When <dry_run> is "1", no `rm -rf` is executed but the same
#     KEEP/PROTECT/DELETE lines are emitted for inspection.
#
# Emits one line per candidate to stdout:
#   KEEP <path>     kept by newest-first window
#   PROTECT <path>  would delete, but path contains tracked contents
#   DELETE <path>   deleted (or would be deleted when dry_run=1)

_smoke_enumerate_dirs() {
    local smoke_root="$1"
    local pattern="$2"
    if [ -z "$smoke_root" ] || [ ! -d "$smoke_root" ]; then
        return 0
    fi
    find "$smoke_root" -maxdepth 1 -mindepth 1 -type d -name "$pattern" -printf '%T@ %p\n' \
        | sort -nr \
        | awk '{print $2}'
}

_smoke_has_tracked_contents() {
    local repo_root="$1"
    local dir="$2"
    if [ -z "$repo_root" ] || [ -z "$dir" ]; then
        return 1
    fi
    git -C "$repo_root" ls-files --error-unmatch -- "$dir" >/dev/null 2>&1
}

prune_smoke_dirs() {
    local smoke_root="$1"
    local pattern="$2"
    local keep_recent="$3"
    local protect_tracked="${4:-0}"
    local dry_run="${5:-0}"
    local -a dirs
    local idx
    local dir
    local repo_root=""

    if [ -z "$smoke_root" ] || [ -z "$pattern" ]; then
        return 0
    fi
    if ! [[ "$keep_recent" =~ ^[0-9]+$ ]]; then
        return 0
    fi

    if [ "$protect_tracked" = "1" ]; then
        repo_root="$(git -C "$smoke_root" rev-parse --show-toplevel 2>/dev/null || true)"
        if [ -z "$repo_root" ]; then
            printf 'prune_smoke_dirs: protect_tracked=1 requires a git-backed smoke root, got %s\n' "$smoke_root" >&2
            return 2
        fi
    fi

    mapfile -t dirs < <(_smoke_enumerate_dirs "$smoke_root" "$pattern")
    if [ "${#dirs[@]}" -eq 0 ]; then
        return 0
    fi
    if [ "${#dirs[@]}" -le "$keep_recent" ]; then
        for dir in "${dirs[@]}"; do
            printf 'KEEP %s\n' "$dir"
        done
        return 0
    fi

    for ((idx=0; idx<${#dirs[@]}; idx++)); do
        dir="${dirs[$idx]}"
        if [ "$idx" -lt "$keep_recent" ]; then
            printf 'KEEP %s\n' "$dir"
            continue
        fi

        if [ "$protect_tracked" = "1" ] && _smoke_has_tracked_contents "$repo_root" "$dir"; then
            printf 'PROTECT %s\n' "$dir"
            continue
        fi

        if [ "$dry_run" != "1" ]; then
            rm -rf -- "$dir"
        fi
        printf 'DELETE %s\n' "$dir"
    done
}

# prune_blocked_smoke_dirs <project_root> <keep_recent>
#
# Canonical caller contract for the blocked-smoke auto-prune path used by
# `.pipeline/smoke-implement-blocked-auto-triage.sh`. Delegates to
# `prune_smoke_dirs` with the fixed blocked-smoke parameters:
#   - smoke_root  = "<project_root>/.pipeline"
#   - pattern     = "live-blocked-smoke-*"
#   - protect_tracked = 1  (checked-in `live-blocked-smoke-*` fixtures survive)
#   - dry_run     = 0
#
# Returns 0 as a no-op when `keep_recent` is empty, non-numeric, or <= 0.
# Keeping this wrapper in the shared lib lets regressions cover the real
# auto-prune caller contract without sourcing the tmux-driven smoke script.
prune_blocked_smoke_dirs() {
    local project_root="$1"
    local keep_recent="${2:-}"

    if [ -z "$project_root" ]; then
        return 0
    fi
    if [ -z "$keep_recent" ]; then
        return 0
    fi
    if ! [[ "$keep_recent" =~ ^[0-9]+$ ]]; then
        return 0
    fi
    if [ "$keep_recent" -le 0 ]; then
        return 0
    fi

    prune_smoke_dirs "$project_root/.pipeline" "live-blocked-smoke-*" \
        "$keep_recent" 1 0 >/dev/null
}

# prune_live_arb_smoke_dirs <project_root> <keep_recent>
#
# Canonical caller contract for the live-arb auto-prune path used by
# `.pipeline/smoke-three-agent-arbitration.sh`. Delegates to
# `prune_smoke_dirs` with the fixed live-arb parameters:
#   - smoke_root  = "<project_root>/.pipeline"
#   - pattern     = "live-arb-smoke-*"
#   - protect_tracked = 0  (all live-arb workspaces are generated; no
#                           checked-in fixtures live under this pattern)
#   - dry_run     = 0
#
# Returns 0 as a no-op when `keep_recent` is empty, non-numeric, or <= 0.
# Keeping this wrapper in the shared lib lets regressions cover the real
# auto-prune caller contract without sourcing the tmux-driven smoke script.
prune_live_arb_smoke_dirs() {
    local project_root="$1"
    local keep_recent="${2:-}"

    if [ -z "$project_root" ]; then
        return 0
    fi
    if [ -z "$keep_recent" ]; then
        return 0
    fi
    if ! [[ "$keep_recent" =~ ^[0-9]+$ ]]; then
        return 0
    fi
    if [ "$keep_recent" -le 0 ]; then
        return 0
    fi

    prune_smoke_dirs "$project_root/.pipeline" "live-arb-smoke-*" \
        "$keep_recent" 0 0 >/dev/null
}
