#!/bin/bash
# ============================================================
# stop-pipeline.sh — 전체 파이프라인 종료
# ============================================================

PROJECT_ROOT="${1:-$(pwd)}"
SESSION="ai-pipeline"

GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

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

# pid 파일 밖에 남은 watcher도 함께 정리
for pattern in \
    "$PROJECT_ROOT/watcher_core.py" \
    "$PROJECT_ROOT/pipeline-watcher-v3.sh" \
    "$PROJECT_ROOT/pipeline-watcher-v3-logged.sh"
do
    pids="$(pgrep -f "$pattern" || true)"
    if [ -n "$pids" ]; then
        kill $pids 2>/dev/null || true
    fi
done

# tmux 세션 종료
if tmux has-session -t "$SESSION" 2>/dev/null; then
    tmux kill-session -t "$SESSION"
    echo -e "${GREEN}  tmux 세션 종료${NC}"
fi

echo -e "${GREEN}완료${NC}"
