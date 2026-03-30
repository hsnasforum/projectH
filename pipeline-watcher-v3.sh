#!/bin/bash
# ============================================================
# AI Pipeline Watcher v3 (Single-Codex / tmux 버전)
# ============================================================

PROJECT_ROOT="${1:-$(pwd)}"
SESSION="ai-pipeline"
WORK_DIR="$PROJECT_ROOT/work"
PIPELINE_DIR="$PROJECT_ROOT/.pipeline"
CODEX_FEEDBACK="$PIPELINE_DIR/codex_feedback.md"

PANE_CLAUDE="$SESSION:0.0"
PANE_CODEX="$SESSION:0.1"

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
CYAN='\033[0;36m'
GRAY='\033[0;37m'
NC='\033[0m'

# ============================================================
# 유틸 함수
# ============================================================

get_latest_file() {
    find "$1" -name "*.md" -type f 2>/dev/null | \
        xargs ls -t 2>/dev/null | head -1
}

get_mtime() {
    stat -c %Y "$1" 2>/dev/null || echo 0
}

send_to_pane() {
    local pane="$1"
    local msg="$2"
    # 텍스트 입력
    tmux send-keys -t "$pane" "$msg" ""
    # Enter 전에 충분히 대기
    sleep 0.5
    # Enter 전송
    tmux send-keys -t "$pane" "" Enter
    sleep 0.3
}

# ============================================================
# 단계별 핸들러
# ============================================================

handle_work_updated() {
    local filepath="$1"
    echo ""
    echo -e "${CYAN}┌─────────────────────────────────────────${NC}"
    echo -e "${CYAN}│ [STEP 1] Claude 작업완료 감지${NC}"
    echo -e "${CYAN}│  파일: $(basename "$filepath")${NC}"
    echo -e "${CYAN}└─────────────────────────────────────────${NC}"

    local msg="AGENTS.md, work/README.md, verify/README.md, .pipeline/README.md를 먼저 읽고, 최신 /work와 같은 날 최신 /verify를 기준으로 코드/문서 truth를 교차확인한 뒤 필요한 검증을 재실행해줘. 결과는 /verify에 남기고, 다음 Claude 지시사항은 .pipeline/codex_feedback.md에 갱신해줘."

    send_to_pane "$PANE_CODEX" "$msg"

    echo -e "${GREEN}  ✓ Codex pane에 전송 완료${NC}"
    echo -e "${GRAY}  → Codex가 .pipeline/codex_feedback.md 저장하면 Claude에 자동 전달됩니다${NC}"
    echo ""
}

handle_codex_feedback_updated() {
    echo ""
    echo -e "${GREEN}┌─────────────────────────────────────────${NC}"
    echo -e "${GREEN}│ [STEP 2] Codex 지시사항 감지${NC}"
    echo -e "${GREEN}│  → Claude pane에 자동 전송 중...${NC}"
    echo -e "${GREEN}└─────────────────────────────────────────${NC}"

    local msg=".pipeline/codex_feedback.md 읽고 다음 작업 진행해줘."

    send_to_pane "$PANE_CLAUDE" "$msg"

    echo -e "${GREEN}  ✓ Claude pane에 전송 완료${NC}"
    echo -e "${GRAY}  → 다음 루프 대기 중...${NC}"
    echo ""
}

# ============================================================
# 메인 감시 루프
# ============================================================

echo ""
echo -e "${CYAN}============================================${NC}"
echo -e "${CYAN}  AI Pipeline Watcher v3 (Single-Codex)${NC}"
echo -e "${CYAN}============================================${NC}"
echo -e "  프로젝트: $PROJECT_ROOT"
echo ""
echo -e "  감시 대상:"
echo -e "${GRAY}    work/**/*.md                  → Claude 완료 (→ Codex)${NC}"
echo -e "${GRAY}    .pipeline/codex_feedback.md   → Codex 완료 (→ Claude)${NC}"
echo ""
echo -e "${YELLOW}  완전 자동 루프 - 포커스 불필요${NC}"
echo -e "${GRAY}  Ctrl+C 로 종료${NC}"
echo -e "${CYAN}============================================${NC}"
echo ""

START_TIME=$(date +%s)
LAST_WORK_MTIME=$START_TIME
LAST_CODEX_MTIME=$START_TIME
LAST_HANDLED_WORK=$START_TIME
LAST_HANDLED_CODEX=$START_TIME

echo -e "${GREEN}[대기] 파일 변경을 감시하고 있습니다...${NC}"
echo -e "${GRAY}  (시작: $(date '+%Y-%m-%d %H:%M:%S') 이후 파일만 감지)${NC}"
echo ""

while true; do
    sleep 1
    NOW=$(date +%s)

    # --- work/ 감시 ---
    CURRENT_WORK=$(get_latest_file "$WORK_DIR")
    if [ -n "$CURRENT_WORK" ]; then
        CURRENT_WORK_MTIME=$(get_mtime "$CURRENT_WORK")
        FILE_AGE=$((NOW - CURRENT_WORK_MTIME))
        if [ "$CURRENT_WORK_MTIME" -gt "$LAST_WORK_MTIME" ] && \
           [ "$CURRENT_WORK_MTIME" -gt "$START_TIME" ] && \
           [ "$FILE_AGE" -gt 1 ] && [ "$FILE_AGE" -lt 10 ] && \
           [ "$CURRENT_WORK_MTIME" -ne "$LAST_HANDLED_WORK" ]; then
            LAST_WORK_MTIME=$CURRENT_WORK_MTIME
            LAST_HANDLED_WORK=$CURRENT_WORK_MTIME
            handle_work_updated "$CURRENT_WORK"
        fi
    fi

    # --- .pipeline/codex_feedback.md 감시 ---
    if [ -f "$CODEX_FEEDBACK" ]; then
        CURRENT_CODEX_MTIME=$(get_mtime "$CODEX_FEEDBACK")
        FILE_AGE=$((NOW - CURRENT_CODEX_MTIME))
        if [ "$CURRENT_CODEX_MTIME" -gt "$LAST_CODEX_MTIME" ] && \
           [ "$CURRENT_CODEX_MTIME" -gt "$START_TIME" ] && \
           [ "$FILE_AGE" -gt 1 ] && [ "$FILE_AGE" -lt 10 ] && \
           [ "$CURRENT_CODEX_MTIME" -ne "$LAST_HANDLED_CODEX" ]; then
            LAST_CODEX_MTIME=$CURRENT_CODEX_MTIME
            LAST_HANDLED_CODEX=$CURRENT_CODEX_MTIME
            handle_codex_feedback_updated
        fi
    fi
done
