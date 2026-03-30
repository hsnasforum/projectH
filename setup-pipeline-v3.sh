#!/bin/bash
# ============================================================
# AI Pipeline - tmux 셋업 스크립트 v3
# Single-Codex 구조 (Claude / Codex / Watcher)
# ============================================================

PROJECT_ROOT="${1:-$(pwd)}"
SESSION="ai-pipeline"

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
CYAN='\033[0;36m'
GRAY='\033[0;37m'
NC='\033[0m'

echo ""
echo -e "${CYAN}============================================${NC}"
echo -e "${CYAN}  AI Pipeline 셋업 v3 (Single-Codex)${NC}"
echo -e "${CYAN}============================================${NC}"
echo -e "  프로젝트: $PROJECT_ROOT"
echo ""

# 1. tmux 설치 확인
if ! command -v tmux &>/dev/null; then
    echo -e "${YELLOW}[설치] tmux 설치 중...${NC}"
    sudo apt-get update -qq && sudo apt-get install -y tmux
    echo -e "${GREEN}[완료] tmux 설치됨${NC}"
else
    echo -e "${GREEN}[확인] tmux $(tmux -V) 이미 설치됨${NC}"
fi

# 2. .pipeline 폴더 초기화 (codex_feedback.md 만 유지)
PIPELINE_DIR="$PROJECT_ROOT/.pipeline"
mkdir -p "$PIPELINE_DIR"
[ ! -f "$PIPELINE_DIR/codex_feedback.md" ] && echo "" > "$PIPELINE_DIR/codex_feedback.md"
echo -e "${GREEN}[확인] .pipeline 폴더 준비됨${NC}"

# 3. 기존 세션 정리
tmux kill-session -t "$SESSION" 2>/dev/null && \
    echo -e "${YELLOW}[정리] 기존 세션 종료${NC}"

# 4. tmux 세션 생성
echo -e "${YELLOW}[생성] tmux 세션 구성 중...${NC}"

tmux new-session -d -s "$SESSION" -x 220 -y 50
tmux rename-window -t "$SESSION" "pipeline"

# pane 분할 (3개)
# 좌: Claude / 우상: Codex / 우하: Watcher
tmux split-window -t "$SESSION:0.0" -h
tmux split-window -t "$SESSION:0.1" -v

# 5. tmux 옵션
tmux set-option -t "$SESSION" remain-on-exit on
tmux set-option -t "$SESSION" mouse on

# 6. 각 pane 초기화

# pane 0: Claude CLI (좌측 전체)
tmux send-keys -t "$SESSION:0.0" "cd $PROJECT_ROOT" Enter
sleep 0.8
tmux send-keys -t "$SESSION:0.0" "echo '=== Claude (구현) ===' && claude" Enter
sleep 1.5

# pane 1: Codex (우상단 - 교차분석 + 검증 + 지시문 작성)
tmux send-keys -t "$SESSION:0.1" "cd $PROJECT_ROOT" Enter
sleep 0.8
tmux send-keys -t "$SESSION:0.1" "echo '=== Codex (검증) ===' && codex" Enter
sleep 1.5

# pane 2: Watcher (우하단)
tmux send-keys -t "$SESSION:0.2" "cd $PROJECT_ROOT" Enter
sleep 0.8
tmux send-keys -t "$SESSION:0.2" "echo '=== Pipeline Watcher ===' && ./pipeline-watcher-v3.sh $PROJECT_ROOT" Enter

# 7. 완료
echo ""
echo -e "${GREEN}============================================${NC}"
echo -e "${GREEN}  셋업 완료!${NC}"
echo -e "${GREEN}============================================${NC}"
echo ""
echo -e "  레이아웃:"
echo -e "${CYAN}  ┌───────────────┬───────────────┐${NC}"
echo -e "${CYAN}  │               │  pane 1       │${NC}"
echo -e "${CYAN}  │  pane 0       │  Codex        │${NC}"
echo -e "${CYAN}  │  Claude       │  (검증)       │${NC}"
echo -e "${CYAN}  │  (구현)       ├───────────────┤${NC}"
echo -e "${CYAN}  │               │  pane 2       │${NC}"
echo -e "${CYAN}  │               │  Watcher      │${NC}"
echo -e "${CYAN}  └───────────────┴───────────────┘${NC}"
echo ""
echo -e "  단축키:"
echo -e "${GRAY}    마우스 클릭      : pane 이동${NC}"
echo -e "${GRAY}    Ctrl+B 방향키    : pane 이동${NC}"
echo -e "${GRAY}    Ctrl+B D         : detach (백그라운드 유지)${NC}"
echo -e "${GRAY}    Ctrl+B Z         : 현재 pane 전체화면${NC}"
echo -e "${GRAY}    tmux attach -t $SESSION : 재접속${NC}"
echo ""

tmux attach-session -t "$SESSION"
