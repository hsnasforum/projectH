#!/bin/bash
# ============================================================
# start-pipeline.sh
# 사용법:
#   bash start-pipeline.sh .                     # 기본: experimental
#   bash start-pipeline.sh . --mode baseline     # baseline만
#   bash start-pipeline.sh . --mode experimental # experimental만
#   bash start-pipeline.sh . --mode both         # 둘 다 (비교 불가, 비권장)
# ============================================================

PROJECT_ROOT="${1:-$(pwd)}"
MODE="experimental"

for arg in "$@"; do
    case $arg in
        baseline|experimental|both) MODE="$arg" ;;
    esac
done

SESSION="ai-pipeline"
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

GREEN='\033[0;32m'
CYAN='\033[0;36m'
YELLOW='\033[1;33m'
GRAY='\033[0;37m'
NC='\033[0m'

echo ""
echo -e "${CYAN}============================================${NC}"
echo -e "${CYAN}  AI Pipeline Launcher  [mode: $MODE]${NC}"
echo -e "${CYAN}============================================${NC}"
echo -e "  프로젝트: $PROJECT_ROOT"
echo ""

# ------------------------------------------------------------
# 1. 기존 프로세스 정리
# ------------------------------------------------------------
echo -e "${YELLOW}[1/4] 기존 프로세스 정리 중...${NC}"

if tmux has-session -t "$SESSION" 2>/dev/null; then
    tmux kill-session -t "$SESSION"
fi

for pidfile in baseline experimental; do
    pf="$PROJECT_ROOT/.pipeline/$pidfile.pid"
    if [ -f "$pf" ]; then
        kill "$(cat "$pf")" 2>/dev/null
        rm "$pf"
    fi
done

# ------------------------------------------------------------
# 2. 로그/상태 초기화 (모드별)
# ------------------------------------------------------------
if [ "$MODE" = "baseline" ] || [ "$MODE" = "both" ]; then
    rm -rf "$PROJECT_ROOT/.pipeline/logs/baseline"
    mkdir -p "$PROJECT_ROOT/.pipeline/logs/baseline"
    echo -e "${GRAY}  baseline 로그 초기화${NC}"
fi

if [ "$MODE" = "experimental" ] || [ "$MODE" = "both" ]; then
    rm -rf "$PROJECT_ROOT/.pipeline/logs/experimental"
    rm -rf "$PROJECT_ROOT/.pipeline/state"
    rm -rf "$PROJECT_ROOT/.pipeline/locks"
    rm -rf "$PROJECT_ROOT/.pipeline/manifests"
    mkdir -p "$PROJECT_ROOT/.pipeline/logs/experimental"
    mkdir -p "$PROJECT_ROOT/.pipeline/state"
    mkdir -p "$PROJECT_ROOT/.pipeline/locks"
    mkdir -p "$PROJECT_ROOT/.pipeline/manifests"
    echo -e "${GRAY}  experimental 로그/state/locks/manifests 초기화${NC}"
fi

# ------------------------------------------------------------
# 3. tmux 세션 생성
# ------------------------------------------------------------
echo -e "${GREEN}[2/4] tmux 세션 생성 중...${NC}"

tmux new-session -d -s "$SESSION"
tmux split-window -h -t "$SESSION:0"
tmux send-keys -t "$SESSION:0.0" "cd '$PROJECT_ROOT' && claude --dangerously-skip-permissions" Enter
tmux send-keys -t "$SESSION:0.1" "cd '$PROJECT_ROOT' && codex" Enter

echo -e "${GRAY}  tmux: $SESSION (0.0=Claude / 0.1=Codex)${NC}"
sleep 2

# ------------------------------------------------------------
# 4. watcher 실행
# ------------------------------------------------------------
if [ "$MODE" = "baseline" ] || [ "$MODE" = "both" ]; then
    echo -e "${GREEN}[3/4] baseline watcher 시작 중...${NC}"
    bash "$SCRIPT_DIR/pipeline-watcher-v3-logged.sh" "$PROJECT_ROOT" \
        > "$PROJECT_ROOT/.pipeline/logs/baseline/watcher.log" 2>&1 &
    echo $! > "$PROJECT_ROOT/.pipeline/baseline.pid"
    echo -e "${GRAY}  baseline PID: $(cat "$PROJECT_ROOT/.pipeline/baseline.pid")${NC}"
else
    echo -e "${GRAY}[3/4] baseline 건너뜀${NC}"
fi

if [ "$MODE" = "experimental" ] || [ "$MODE" = "both" ]; then
    echo -e "${GREEN}[4/4] experimental watcher 시작 중...${NC}"
    VERIFY_PROMPT="AGENTS.md, work/README.md, verify/README.md, .pipeline/README.md를 먼저 읽고, 최신 Claude /work와 같은 날 최신 /verify를 기준으로 이번 라운드 변경만 검수해줘. Claude가 주장한 코드/문서 변경이 실제로 맞는지, 범위가 현재 projectH 방향에서 벗어나지 않았는지 확인하고, 이번 변경에 필요한 검증만 재실행해줘. 결과는 /verify에 남기고, 다음 Claude 지시사항은 .pipeline/codex_feedback.md에 갱신해줘. 전체 프로젝트 진단이 필요하면 /verify가 아니라 report/에 분리해줘."
    CLAUDE_PROMPT="AGENTS.md, work/README.md, .pipeline/codex_feedback.md를 읽고 다음 작업을 진행해줘."
    python3 "$SCRIPT_DIR/watcher_core.py" \
        --watch-dir "$PROJECT_ROOT/work" \
        --base-dir "$PROJECT_ROOT/.pipeline" \
        --verify-pane-target "$SESSION:0.1" \
        --claude-pane-target "$SESSION:0.0" \
        --verify-prompt "$VERIFY_PROMPT" \
        --claude-prompt "$CLAUDE_PROMPT" \
        --lease-ttl 120 \
        > "$PROJECT_ROOT/.pipeline/logs/experimental/watcher.log" 2>&1 &
    echo $! > "$PROJECT_ROOT/.pipeline/experimental.pid"
    echo -e "${GRAY}  experimental PID: $(cat "$PROJECT_ROOT/.pipeline/experimental.pid")${NC}"
else
    echo -e "${GRAY}[4/4] experimental 건너뜀${NC}"
fi

# ------------------------------------------------------------
# 완료 안내
# ------------------------------------------------------------
echo ""
echo -e "${CYAN}============================================${NC}"
echo -e "${GREEN}  파이프라인 실행 완료 [mode: $MODE]${NC}"
echo -e "${CYAN}============================================${NC}"
echo ""
echo -e "  tmux 접속:  ${YELLOW}tmux attach -t $SESSION${NC}"
echo -e "  A/B 집계:   ${YELLOW}python3 ab_compare.py .pipeline/logs${NC}"
echo -e "  전체 종료:  ${YELLOW}bash stop-pipeline.sh${NC}"
echo ""
if [ "$MODE" = "both" ]; then
    echo -e "${YELLOW}  ※ both 모드는 A/B 비교에 적합하지 않습니다.${NC}"
    echo ""
fi

tmux attach -t "$SESSION"
