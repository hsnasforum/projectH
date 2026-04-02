#!/bin/bash
# ============================================================
# AI Pipeline Watcher v3 (Single-Codex / tmux 버전)
# + thin JSONL logging for baseline A/B comparison
# ============================================================

PROJECT_ROOT="${1:-$(pwd)}"
SESSION="ai-pipeline"
WORK_DIR="$PROJECT_ROOT/work"
PIPELINE_DIR="$PROJECT_ROOT/.pipeline"
CODEX_FEEDBACK="$PIPELINE_DIR/codex_feedback.md"
LOG_DIR="$PIPELINE_DIR/logs/baseline"
RAW_LOG="$LOG_DIR/raw.jsonl"
SUPPRESSED_LOG="$LOG_DIR/suppressed.jsonl"
DISPATCH_LOG="$LOG_DIR/dispatch.jsonl"

# Accept pane IDs as arguments, fallback to index
PANE_CLAUDE="${2:-$SESSION:0.0}"
PANE_CODEX="${3:-$SESSION:0.1}"

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
CYAN='\033[0;36m'
GRAY='\033[0;37m'
NC='\033[0m'

mkdir -p "$LOG_DIR"
touch "$RAW_LOG" "$SUPPRESSED_LOG" "$DISPATCH_LOG"

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

json_escape() {
    local s="$1"
    s=${s//\\/\\\\}
    s=${s//"/\\"}
    s=${s//$'\n'/\\n}
    s=${s//$'\r'/\\r}
    s=${s//$'\t'/\\t}
    printf '%s' "$s"
}

now_ts() {
    date +%s.%N
}

relative_path() {
    local path="$1"
    local rel
    rel="${path#"$PROJECT_ROOT"/}"
    if [ "$rel" = "$path" ]; then
        rel="$(basename "$path")"
    fi
    printf '%s' "$rel"
}

make_job_id() {
    local path="$1"
    local rel stem safe_stem path_hash date_part
    rel="$(relative_path "$path")"
    stem="$(basename "$path" .md)"
    safe_stem="$(printf '%s' "$stem" | tr '[:space:]/' '--' | tr -cd '[:alnum:]_.-')"
    [ -z "$safe_stem" ] && safe_stem="artifact"
    path_hash="$(printf '%s' "$rel" | sha1sum | awk '{print substr($1,1,8)}')"
    date_part="$(date '+%Y%m%d')"
    printf '%s-%s-%s' "$date_part" "$safe_stem" "$path_hash"
}

append_jsonl() {
    local logfile="$1"
    local json_line="$2"
    printf '%s\n' "$json_line" >> "$logfile"
}

log_raw() {
    local path="$1"
    local slot="$2"
    local event_name="${3:-artifact_seen}"
    local job_id rel at
    rel="$(relative_path "$path")"
    job_id="$(make_job_id "$path")"
    at="$(now_ts)"
    append_jsonl "$RAW_LOG" "{\"event\":\"$(json_escape "$event_name")\",\"path\":\"$(json_escape "$rel")\",\"job_id\":\"$(json_escape "$job_id")\",\"slot\":\"$(json_escape "$slot")\",\"at\":$at}"
}

log_suppressed() {
    local path="$1"
    local slot="$2"
    local reason="$3"
    local job_id at
    job_id="$(make_job_id "$path")"
    at="$(now_ts)"
    append_jsonl "$SUPPRESSED_LOG" "{\"event\":\"suppressed\",\"job_id\":\"$(json_escape "$job_id")\",\"slot\":\"$(json_escape "$slot")\",\"reason\":\"$(json_escape "$reason")\",\"at\":$at}"
}

log_dispatch() {
    local path="$1"
    local slot="$2"
    local pane="$3"
    local job_id at
    job_id="$(make_job_id "$path")"
    at="$(now_ts)"
    append_jsonl "$DISPATCH_LOG" "{\"event\":\"dispatch\",\"job_id\":\"$(json_escape "$job_id")\",\"slot\":\"$(json_escape "$slot")\",\"pane\":\"$(json_escape "$pane")\",\"dry_run\":false,\"at\":$at}"
}

send_to_pane() {
    local pane="$1"
    local msg="$2"
    # set-buffer + paste-buffer for reliable long text dispatch
    tmux set-buffer "$msg"
    tmux paste-buffer -t "$pane"
    sleep 1.5
    tmux send-keys -t "$pane" Enter
    sleep 0.5
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
    log_dispatch "$filepath" "slot_verify" "$PANE_CODEX"

    echo -e "${GREEN}  ✓ Codex pane에 전송 완료${NC}"
    echo -e "${GRAY}  → Codex가 .pipeline/codex_feedback.md 저장하면 Claude에 자동 전달됩니다${NC}"
    echo ""
}

handle_codex_feedback_updated() {
    local filepath="$1"
    echo ""
    echo -e "${GREEN}┌─────────────────────────────────────────${NC}"
    echo -e "${GREEN}│ [STEP 2] Codex 지시사항 감지${NC}"
    echo -e "${GREEN}│  → Claude pane에 자동 전송 중...${NC}"
    echo -e "${GREEN}└─────────────────────────────────────────${NC}"

    local msg="work/README.md,CLAUDE.md, .pipeline/codex_feedback.md 읽고, STATUS가 implement일 때만 그 지시대로 한 슬라이스만 구현해줘. 작업 후 /work closeout 남겨줘."

    send_to_pane "$PANE_CLAUDE" "$msg"
    log_dispatch "$filepath" "slot_claude" "$PANE_CLAUDE"

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
echo -e "${GRAY}    .pipeline/logs/*.jsonl        → baseline A/B 로그${NC}"
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
        log_raw "$CURRENT_WORK" "slot_verify" "artifact_seen"

        if [ "$CURRENT_WORK_MTIME" -le "$LAST_WORK_MTIME" ]; then
            log_suppressed "$CURRENT_WORK" "slot_verify" "not_newer_than_last_work_mtime"
        elif [ "$CURRENT_WORK_MTIME" -le "$START_TIME" ]; then
            log_suppressed "$CURRENT_WORK" "slot_verify" "before_start_time"
        elif [ "$FILE_AGE" -le 1 ]; then
            log_suppressed "$CURRENT_WORK" "slot_verify" "mtime_too_recent"
        elif [ "$FILE_AGE" -ge 10 ]; then
            log_suppressed "$CURRENT_WORK" "slot_verify" "mtime_too_old"
        elif [ "$CURRENT_WORK_MTIME" -eq "$LAST_HANDLED_WORK" ]; then
            log_suppressed "$CURRENT_WORK" "slot_verify" "already_processed"
        else
            LAST_WORK_MTIME=$CURRENT_WORK_MTIME
            LAST_HANDLED_WORK=$CURRENT_WORK_MTIME
            handle_work_updated "$CURRENT_WORK"
        fi
    fi

    # --- .pipeline/codex_feedback.md 감시 ---
    if [ -f "$CODEX_FEEDBACK" ]; then
        CURRENT_CODEX_MTIME=$(get_mtime "$CODEX_FEEDBACK")
        FILE_AGE=$((NOW - CURRENT_CODEX_MTIME))
        log_raw "$CODEX_FEEDBACK" "slot_claude" "artifact_seen"

        if [ "$CURRENT_CODEX_MTIME" -le "$LAST_CODEX_MTIME" ]; then
            log_suppressed "$CODEX_FEEDBACK" "slot_claude" "not_newer_than_last_codex_mtime"
        elif [ "$CURRENT_CODEX_MTIME" -le "$START_TIME" ]; then
            log_suppressed "$CODEX_FEEDBACK" "slot_claude" "before_start_time"
        elif [ "$FILE_AGE" -le 1 ]; then
            log_suppressed "$CODEX_FEEDBACK" "slot_claude" "mtime_too_recent"
        elif [ "$FILE_AGE" -ge 10 ]; then
            log_suppressed "$CODEX_FEEDBACK" "slot_claude" "mtime_too_old"
        elif [ "$CURRENT_CODEX_MTIME" -eq "$LAST_HANDLED_CODEX" ]; then
            log_suppressed "$CODEX_FEEDBACK" "slot_claude" "already_processed"
        else
            LAST_CODEX_MTIME=$CURRENT_CODEX_MTIME
            LAST_HANDLED_CODEX=$CURRENT_CODEX_MTIME
            handle_codex_feedback_updated "$CODEX_FEEDBACK"
        fi
    fi
done
