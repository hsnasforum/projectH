#!/bin/bash
# ============================================================
# AI Pipeline - tmux 셋업 스크립트 — LEGACY / DEPRECATED
# 참고: canonical 버전은 setup-pipeline-v3.sh 입니다.
# ============================================================
# 사용법: ./setup-pipeline.sh [프로젝트경로]
# 예시:   ./setup-pipeline.sh ~/code/projectH
# ============================================================

PROJECT_ROOT="${1:-$(pwd)}"
SESSION="ai-pipeline"

# 색상
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
CYAN='\033[0;36m'
NC='\033[0m'

echo ""
echo -e "${CYAN}============================================${NC}"
echo -e "${CYAN}  AI Pipeline 셋업${NC}"
echo -e "${CYAN}============================================${NC}"
echo -e "  프로젝트: $PROJECT_ROOT"
echo ""

# ============================================================
# 1. tmux 설치 확인 및 설치
# ============================================================
if ! command -v tmux &>/dev/null; then
    echo -e "${YELLOW}[설치] tmux 설치 중...${NC}"
    sudo apt-get update -qq && sudo apt-get install -y tmux
    echo -e "${GREEN}[완료] tmux 설치됨${NC}"
else
    echo -e "${GREEN}[확인] tmux $(tmux -V) 이미 설치됨${NC}"
fi

# ============================================================
# 2. .pipeline 폴더 초기화
# ============================================================
PIPELINE_DIR="$PROJECT_ROOT/.pipeline"
mkdir -p "$PIPELINE_DIR"
[ ! -f "$PIPELINE_DIR/codex_feedback.md" ]  && echo "" > "$PIPELINE_DIR/codex_feedback.md"
echo -e "${GREEN}[확인] .pipeline 폴더 준비됨${NC}"

# ============================================================
# 3. 기존 세션 정리
# ============================================================
tmux kill-session -t "$SESSION" 2>/dev/null && \
    echo -e "${YELLOW}[정리] 기존 세션 종료${NC}"

# ============================================================
# 4. tmux 세션 생성
#
# 레이아웃:
# ┌─────────────────┬─────────────────┐
# │  pane 1         │  pane 2         │
# │  Claude CLI     │  Codex A        │
# │  (구현)         │  (프롬프트생성) │
# ├─────────────────┼─────────────────┤
# │  pane 3         │  pane 4         │
# │  Codex B        │  watcher        │
# │  (검증)         │  (파일감시)     │
# └─────────────────┴─────────────────┘
# ============================================================

echo -e "${YELLOW}[생성] tmux 세션 구성 중...${NC}"

# 세션 생성 (pane 1: Claude CLI)
tmux new-session -d -s "$SESSION" -x 220 -y 50
tmux rename-window -t "$SESSION" "pipeline"

# pane 2: Codex A (프롬프트 생성) - 오른쪽 분할
tmux split-window -t "$SESSION:0" -h

# pane 3: Codex B (검증) - 왼쪽 아래 분할
tmux split-window -t "$SESSION:0.0" -v

# pane 4: watcher - 오른쪽 아래 분할
tmux split-window -t "$SESSION:0.1" -v

# ============================================================
# 5. 각 pane 제목 설정 및 초기화
# ============================================================

# pane 0: Claude CLI
tmux send-keys -t "$SESSION:0.0" "cd $PROJECT_ROOT && printf '\033]2;CLAUDE\033\\'" Enter
tmux send-keys -t "$SESSION:0.0" "echo '=== Claude CLI (구현) ===' && claude" Enter

# pane 1: Codex A (프롬프트 생성)
tmux send-keys -t "$SESSION:0.1" "cd $PROJECT_ROOT && printf '\033]2;CODEX-A\033\\'" Enter
tmux send-keys -t "$SESSION:0.1" "echo '=== Codex A (프롬프트 생성) ===' && codex" Enter

# pane 2: Codex B (검증)
tmux send-keys -t "$SESSION:0.2" "cd $PROJECT_ROOT && printf '\033]2;CODEX-B\033\\'" Enter
tmux send-keys -t "$SESSION:0.2" "echo '=== Codex B (검증) ===' && codex" Enter

# pane 3: watcher
tmux send-keys -t "$SESSION:0.3" "cd $PROJECT_ROOT && printf '\033]2;WATCHER\033\\'" Enter
tmux send-keys -t "$SESSION:0.3" "echo '=== Pipeline Watcher ===' && sleep 1 && ./pipeline-watcher-tmux.sh $PROJECT_ROOT" Enter

# ============================================================
# 6. 세션 attach
# ============================================================
echo ""
echo -e "${GREEN}============================================${NC}"
echo -e "${GREEN}  셋업 완료! tmux 세션 접속 중...${NC}"
echo -e "${GREEN}============================================${NC}"
echo ""
echo -e "  pane 구성:"
echo -e "${CYAN}    좌상단 (pane 0)${NC}: Claude CLI  - 구현"
echo -e "${CYAN}    우상단 (pane 1)${NC}: Codex A     - 프롬프트 생성"
echo -e "${CYAN}    좌하단 (pane 2)${NC}: Codex B     - 검증"
echo -e "${CYAN}    우하단 (pane 3)${NC}: Watcher     - 파일 감시"
echo ""
echo -e "  tmux 단축키:"
echo -e "${GRAY}    Ctrl+B → 방향키  : pane 이동${NC}"
echo -e "${GRAY}    Ctrl+B → D        : 세션 detach (백그라운드 유지)${NC}"
echo -e "${GRAY}    tmux attach -t $SESSION : 다시 접속${NC}"
echo ""

tmux attach-session -t "$SESSION"
