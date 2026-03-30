#!/bin/bash
# ============================================================
# AI Pipeline - tmux 셋업 스크립트 v2 — LEGACY / DEPRECATED
# 참고: canonical 버전은 setup-pipeline-v3.sh 입니다.
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
echo -e "${CYAN}  AI Pipeline 셋업 v2${NC}"
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

# 2. .pipeline 폴더 초기화
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

# pane 분할
tmux split-window -t "$SESSION:0.0" -h  # 우상단 (Codex A)
tmux split-window -t "$SESSION:0.0" -v  # 좌하단 (Codex B)
tmux split-window -t "$SESSION:0.1" -v  # 우하단 (Watcher)

# 5. tmux 옵션 (중요: pane 꺼져도 세션 유지)
tmux set-option -t "$SESSION" remain-on-exit on
tmux set-option -t "$SESSION" mouse on

# 6. 각 pane 초기화 (sleep으로 타이밍 확보)

# pane 0: Claude CLI
tmux send-keys -t "$SESSION:0.0" "cd $PROJECT_ROOT" Enter
sleep 0.8
tmux send-keys -t "$SESSION:0.0" "echo '=== Claude CLI (구현) ===' && claude" Enter
sleep 1.5

# pane 1: Codex A (프롬프트 생성)
tmux send-keys -t "$SESSION:0.1" "cd $PROJECT_ROOT" Enter
sleep 0.8
tmux send-keys -t "$SESSION:0.1" "echo '=== Codex A (프롬프트 생성) ===' && codex" Enter
sleep 1.5

# pane 2: Codex B (검증)
tmux send-keys -t "$SESSION:0.2" "cd $PROJECT_ROOT" Enter
sleep 0.8
tmux send-keys -t "$SESSION:0.2" "echo '=== Codex B (검증) ===' && codex" Enter
sleep 1.5

# pane 3: Watcher
tmux send-keys -t "$SESSION:0.3" "cd $PROJECT_ROOT" Enter
sleep 0.8
tmux send-keys -t "$SESSION:0.3" "echo '=== Pipeline Watcher ===' && ./pipeline-watcher-tmux.sh $PROJECT_ROOT" Enter

# 7. 완료 메시지
echo ""
echo -e "${GREEN}============================================${NC}"
echo -e "${GREEN}  셋업 완료!${NC}"
echo -e "${GREEN}============================================${NC}"
echo ""
echo -e "  레이아웃:"
echo -e "${CYAN}  ┌─────────────────┬─────────────────┐${NC}"
echo -e "${CYAN}  │  pane 0         │  pane 1         │${NC}"
echo -e "${CYAN}  │  Claude CLI     │  Codex A        │${NC}"
echo -e "${CYAN}  │  (구현)         │  (프롬프트생성) │${NC}"
echo -e "${CYAN}  ├─────────────────┼─────────────────┤${NC}"
echo -e "${CYAN}  │  pane 2         │  pane 3         │${NC}"
echo -e "${CYAN}  │  Codex B        │  Watcher        │${NC}"
echo -e "${CYAN}  │  (검증)         │  (파일감시)     │${NC}"
echo -e "${CYAN}  └─────────────────┴─────────────────┘${NC}"
echo ""
echo -e "  단축키:"
echo -e "${GRAY}    마우스 클릭    : pane 이동 (마우스 모드 ON)${NC}"
echo -e "${GRAY}    Ctrl+B 방향키  : pane 이동${NC}"
echo -e "${GRAY}    Ctrl+B D       : detach (백그라운드 유지)${NC}"
echo -e "${GRAY}    Ctrl+B Z       : 현재 pane 전체화면${NC}"
echo -e "${GRAY}    tmux attach -t $SESSION : 재접속${NC}"
echo ""

tmux attach-session -t "$SESSION"
