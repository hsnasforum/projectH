#!/bin/bash
# ============================================================
# AI Pipeline Watcher (tmux 버전) — LEGACY / DEPRECATED
# 참고: canonical 버전은 pipeline-watcher-v3.sh 입니다.
# Single-Codex 흐름: work → Codex → codex_feedback → Claude
# tmux send-keys로 특정 pane에 직접 전송
# 포커스 없이 백그라운드 동작
#
# NOTE: 이 스크립트는 dual-Codex 시절 만들어졌으나,
# single-Codex 정책에 맞춰 gpt_prompt.md 의존을 제거했습니다.
# 새 환경에서는 setup-pipeline-v3.sh + pipeline-watcher-v3.sh를
# 사용하세요.
# ============================================================

PROJECT_ROOT="${1:-$(pwd)}"
SESSION="ai-pipeline"
WORK_DIR="$PROJECT_ROOT/work"
PIPELINE_DIR="$PROJECT_ROOT/.pipeline"
CODEX_FEEDBACK="$PIPELINE_DIR/codex_feedback.md"

# pane 인덱스
PANE_CLAUDE="$SESSION:0.0"
PANE_CODEX="$SESSION:0.1"

# 색상
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
CYAN='\033[0;36m'
MAGENTA='\033[0;35m'
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

# tmux pane에 텍스트 전송 (포커스 불필요)
send_to_pane() {
    local pane="$1"
    local content="$2"

    # 긴 텍스트는 파일을 통해 전송 (직접 send-keys는 길이 제한 있음)
    local tmpfile=$(mktemp /tmp/pipeline_XXXXXX.txt)
    echo "$content" > "$tmpfile"

    # tmux load-buffer + paste-buffer 방식 (가장 안정적)
    tmux load-buffer "$tmpfile"
    tmux paste-buffer -t "$pane"
    sleep 0.3
    tmux send-keys -t "$pane" "" Enter

    rm -f "$tmpfile"
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

    local content=$(cat "$filepath")
    if [ -z "$(echo "$content" | tr -d '[:space:]')" ]; then
        echo -e "${RED}  [경고] 파일이 비어있습니다${NC}"
        return
    fi

    # Codex pane에 검증 요청 전송
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
echo -e "${CYAN}  AI Pipeline Watcher (tmux 버전)${NC}"
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

# 초기 상태 스냅샷
LAST_WORK=$(get_latest_file "$WORK_DIR")
LAST_WORK_MTIME=$([ -n "$LAST_WORK" ] && get_mtime "$LAST_WORK" || echo 0)
LAST_CODEX_MTIME=$(get_mtime "$CODEX_FEEDBACK")

LAST_HANDLED_WORK=0
LAST_HANDLED_CODEX=0

echo -e "${GREEN}[대기] 파일 변경을 감시하고 있습니다...${NC}"
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
           [ "$FILE_AGE" -gt 1 ] && [ "$FILE_AGE" -lt 10 ] && \
           [ "$CURRENT_CODEX_MTIME" -ne "$LAST_HANDLED_CODEX" ]; then
            LAST_CODEX_MTIME=$CURRENT_CODEX_MTIME
            LAST_HANDLED_CODEX=$CURRENT_CODEX_MTIME
            handle_codex_feedback_updated
        fi
    fi
done
