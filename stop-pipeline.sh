#!/bin/bash
# ============================================================
# stop-pipeline.sh — 전체 파이프라인 종료
# ============================================================

PROJECT_ROOT="${1:-$(pwd)}"
SESSION=""

# Parse --session
prev=""
for arg in "$@"; do
    case $arg in
        --session=*) SESSION="${arg#*=}" ;;
    esac
    if [ "$prev" = "--session" ]; then SESSION="$arg"; fi
    prev="$arg"
done

# Default: project-aware session name
if [ -z "$SESSION" ]; then
    _proj_name="$(basename "$(readlink -f "$PROJECT_ROOT")")"
    _safe_name="$(printf '%s' "$_proj_name" | tr -cd 'A-Za-z0-9_-')"
    SESSION="aip-${_safe_name:-default}"
fi

GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

terminate_repo_watchers() {
    local project_abs
    project_abs="$(readlink -f "$PROJECT_ROOT")"
    local pids pid cmd cwd

    pids="$(pgrep -f 'watcher_core\.py|pipeline-watcher-v3(\-logged)?\.sh' || true)"
    for pid in $pids; do
        cmd="$(tr '\0' ' ' < "/proc/$pid/cmdline" 2>/dev/null || true)"
        cwd="$(readlink -f "/proc/$pid/cwd" 2>/dev/null || true)"
        case "$cmd" in
            *watcher_core.py*|*pipeline-watcher-v3.sh*|*pipeline-watcher-v3-logged.sh*)
                if [ "$cwd" = "$project_abs" ] || printf '%s' "$cmd" | grep -Fq "$project_abs"; then
                    kill "$pid" 2>/dev/null || true
                fi
                ;;
        esac
    done
}

echo -e "${YELLOW}파이프라인 종료 중...${NC}"

# baseline watcher 종료
if [ -f "$PROJECT_ROOT/.pipeline/baseline.pid" ]; then
    kill "$(cat "$PROJECT_ROOT/.pipeline/baseline.pid")" 2>/dev/null
    rm "$PROJECT_ROOT/.pipeline/baseline.pid"
    echo -e "${GREEN}  baseline watcher 종료${NC}"
fi

# experimental watcher 종료
if [ -f "$PROJECT_ROOT/.pipeline/experimental.pid" ]; then
    kill "$(cat "$PROJECT_ROOT/.pipeline/experimental.pid")" 2>/dev/null
    rm "$PROJECT_ROOT/.pipeline/experimental.pid"
    echo -e "${GREEN}  experimental watcher 종료${NC}"
fi

# token collector 종료
if [ -f "$PROJECT_ROOT/.pipeline/usage/collector.pid" ]; then
    kill "$(cat "$PROJECT_ROOT/.pipeline/usage/collector.pid")" 2>/dev/null || true
    rm "$PROJECT_ROOT/.pipeline/usage/collector.pid"
    echo -e "${GREEN}  token collector 종료${NC}"
fi
rm -f "$PROJECT_ROOT/.pipeline/usage/collector.pane_id" 2>/dev/null || true
rm -f "$PROJECT_ROOT/.pipeline/usage/collector.window_name" 2>/dev/null || true
rm -f "$PROJECT_ROOT/.pipeline/usage/collector.launch_mode" 2>/dev/null || true

# pid 파일 밖에 남은 repo-local watcher도 함께 정리
terminate_repo_watchers

# tmux 세션 종료
if tmux has-session -t "$SESSION" 2>/dev/null; then
    tmux kill-session -t "$SESSION"
    echo -e "${GREEN}  tmux 세션 종료${NC}"
fi

echo -e "${GREEN}완료${NC}"
