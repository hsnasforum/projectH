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
    tmux send-keys -t "$pane" "$msg" ""
    sleep 0.5
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

    local msg="AGENTS.md, work/README.md, verify/README.md, .pipeline/README.md를 먼저 읽고, 최신 Claude /work를 기준으로 이번 라운드 작업만 검수해줘. 같은 날 최신 /verify를 참고해 현재 truth를 맞추고, 이번 변경에 필요한 검증만 다시 실행해 /verify에 남겨줘. 그다음 Claude가 바로 구현할 수 있는 정확한 다음 단일 슬라이스를 .pipeline/codex_feedback.md에 작성해줘. Claude에게 슬라이스 선택을 넘기지 마. 단일 슬라이스를 확정할 수 없으면 .pipeline/codex_feedback.md에 STATUS: needs_operator만 남겨줘. 전체 프로젝트 audit이 필요하면 /verify가 아니라 report/에 분리해줘."

    send_to_pane "$PANE_CODEX" "$msg"

    echo -e "${GREEN}  ✓ Codex pane에 전송 완료${NC}"
    echo -e "${GRAY}  → Codex가 .pipeline/codex_feedback.md 저장하면 STATUS 확인 후 분기합니다${NC}"
    echo ""
}

handle_codex_feedback_updated() {
    echo ""
    echo -e "${GREEN}┌─────────────────────────────────────────${NC}"
    echo -e "${GREEN}│ [STEP 2] Codex 지시사항 감지${NC}"
    echo -e "${GREEN}│  STATUS 확인 중...${NC}"
    echo -e "${GREEN}└─────────────────────────────────────────${NC}"

    # STATUS 파싱
    local status
    status="$(grep -E '^STATUS:' "$CODEX_FEEDBACK" | head -n1 | cut -d':' -f2 | xargs)"

    echo -e "  STATUS: ${YELLOW}${status:-없음}${NC}"

    if [ "$status" = "implement" ]; then
        # Claude에 자동 전달
        echo -e "${GREEN}  → implement 확인 → Claude pane에 자동 전송 중...${NC}"
        send_to_pane "$PANE_CLAUDE" ".pipeline/codex_feedback.md 읽고, STATUS가 implement일 때만 그 지시대로 한 슬라이스만 구현해줘. 작업 후 /work closeout 남겨줘."
        echo -e "${GREEN}  ✓ Claude pane에 전송 완료${NC}"
        echo -e "${GRAY}  → 다음 루프 대기 중...${NC}"

    elif [ "$status" = "needs_operator" ]; then
        # 자동 전달 금지, 사용자 알림만
        echo ""
        echo -e "${RED}  ══════════════════════════════════════${NC}"
        echo -e "${RED}  ★ OPERATOR 확인 필요                  ${NC}"
        echo -e "${RED}  ══════════════════════════════════════${NC}"
        echo -e "${YELLOW}  자동 전달을 중단했습니다.${NC}"
        echo -e "${YELLOW}  .pipeline/codex_feedback.md 를 확인하고${NC}"
        echo -e "${YELLOW}  직접 Claude에 지시해 주세요.${NC}"
        echo -e "${RED}  ══════════════════════════════════════${NC}"
        # 터미널 벨 알림
        echo -e "\a"

    else
        # STATUS 없거나 미정 → 자동 전달 금지
        echo ""
        echo -e "${RED}  ══════════════════════════════════════${NC}"
        echo -e "${RED}  ★ STATUS 미정 - 자동 전달 중단        ${NC}"
        echo -e "${RED}  ══════════════════════════════════════${NC}"
        echo -e "${YELLOW}  codex_feedback.md에 STATUS가 없습니다.${NC}"
        echo -e "${YELLOW}  STATUS: implement 또는 needs_operator${NC}"
        echo -e "${YELLOW}  형식으로 첫 줄에 추가 후 수동 진행해 주세요.${NC}"
        echo -e "${RED}  ══════════════════════════════════════${NC}"
        echo -e "\a"
    fi
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
echo -e "${GRAY}    .pipeline/codex_feedback.md   → Codex 완료 (STATUS 분기)${NC}"
echo ""
echo -e "  STATUS 분기 규칙:"
echo -e "${GREEN}    STATUS: implement    → Claude 자동 전달${NC}"
echo -e "${RED}    STATUS: needs_operator → 자동 전달 중단, 사용자 알림${NC}"
echo -e "${RED}    STATUS 없음           → 자동 전달 중단, 사용자 알림${NC}"
echo ""
echo -e "${YELLOW}  Ctrl+C 로 종료${NC}"
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
