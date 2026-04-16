#!/bin/bash
set -euo pipefail

PROJECT_ROOT="${1:-$(pwd)}"
PROJECT_ROOT="$(cd "$PROJECT_ROOT" && pwd)"
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
SESSION="${PIPELINE_SMOKE_SESSION:-ai-pipeline-smoke}"
STARTUP_GRACE="${PIPELINE_SMOKE_STARTUP_GRACE:-8}"
TIMEOUT_SEC="${PIPELINE_SMOKE_TIMEOUT:-180}"
KEEP_SESSION_ON_FAILURE="${PIPELINE_SMOKE_KEEP_SESSION_ON_FAILURE:-1}"
KEEP_SESSION_ON_SUCCESS="${PIPELINE_SMOKE_KEEP_SESSION_ON_SUCCESS:-0}"
KEEP_RECENT_SMOKES="${PIPELINE_SMOKE_KEEP_RECENT:-3}"

BASE_DIR="$(mktemp -d "$PROJECT_ROOT/.pipeline/live-arb-smoke-XXXXXX")"
BASE_REL="${BASE_DIR#$PROJECT_ROOT/}"
REPORT_DIR="$BASE_DIR/report/gemini"
WATCHER_LOG="$BASE_DIR/watcher.log"
GEMINI_REQUEST="$BASE_DIR/gemini_request.md"
GEMINI_ADVICE="$BASE_DIR/gemini_advice.md"
CLAUDE_HANDOFF="$BASE_DIR/claude_handoff.md"
OPERATOR_REQUEST="$BASE_DIR/operator_request.md"
SMOKE_WORK_DIR="$BASE_DIR/work/4/3"
SMOKE_VERIFY_DIR="$BASE_DIR/verify/4/3"
SMOKE_WORK_NOTE="$SMOKE_WORK_DIR/2026-04-03-live-arbitration-smoke-work.md"
SMOKE_VERIFY_NOTE="$SMOKE_VERIFY_DIR/2026-04-03-live-arbitration-smoke-verify.md"
SUCCESS=0
WATCHER_PID=""

wait_for_cli_ready() {
    local pane_target="$1"
    local timeout_sec="${2:-20}"
    local started_at
    local pane_text

    started_at="$(date +%s)"
    while true; do
        pane_text="$(tmux capture-pane -pt "$pane_target" -S -20 2>/dev/null || true)"
        if printf '%s\n' "$pane_text" | awk 'NF { print }' | tail -n 12 | grep -Eq '^[[:space:]]*(>|›|❯)([[:space:]].*)?$|[$][[:space:]]*$'; then
            return 0
        fi
        if [ $(( $(date +%s) - started_at )) -ge "$timeout_sec" ]; then
            return 1
        fi
        sleep 1
    done
}

read_status() {
    local path="$1"
    if [ ! -f "$path" ]; then
        return 1
    fi
    awk -F':' '/^STATUS:/ {gsub(/^[[:space:]]+|[[:space:]]+$/, "", $2); print tolower($2); exit}' "$path"
}

read_header_value() {
    local path="$1"
    local key="$2"
    if [ ! -f "$path" ]; then
        return 1
    fi
    awk -F':' -v key="$key" '$1 == key {sub(/^[[:space:]]+/, "", $2); sub(/[[:space:]]+$/, "", $2); print $2; exit}' "$path"
}

wait_for_status() {
    local path="$1"
    local expected="$2"
    local timeout_sec="$3"
    local started_at
    local current

    started_at="$(date +%s)"
    while true; do
        current="$(read_status "$path" 2>/dev/null || true)"
        if [ "$current" = "$expected" ]; then
            return 0
        fi
        if [ $(( $(date +%s) - started_at )) -ge "$timeout_sec" ]; then
            return 1
        fi
        sleep 1
    done
}

wait_for_final_slot() {
    local timeout_sec="$1"
    local started_at
    local handoff_status
    local operator_status

    started_at="$(date +%s)"
    while true; do
        handoff_status="$(read_status "$CLAUDE_HANDOFF" 2>/dev/null || true)"
        operator_status="$(read_status "$OPERATOR_REQUEST" 2>/dev/null || true)"
        if [ "$handoff_status" = "implement" ] || [ "$operator_status" = "needs_operator" ]; then
            return 0
        fi
        if [ $(( $(date +%s) - started_at )) -ge "$timeout_sec" ]; then
            return 1
        fi
        sleep 1
    done
}

prune_old_smoke_dirs() {
    local keep_recent="$1"
    local smoke_root
    local -a dirs
    local idx

    if ! [[ "$keep_recent" =~ ^[0-9]+$ ]]; then
        return 0
    fi
    if [ "$keep_recent" -le 0 ]; then
        return 0
    fi

    smoke_root="$PROJECT_ROOT/.pipeline"
    mapfile -t dirs < <(find "$smoke_root" -maxdepth 1 -mindepth 1 -type d -name 'live-arb-smoke-*' -printf '%T@ %p\n' | sort -nr | awk '{print $2}')
    if [ "${#dirs[@]}" -le "$keep_recent" ]; then
        return 0
    fi

    for ((idx=keep_recent; idx<${#dirs[@]}; idx++)); do
        rm -rf -- "${dirs[$idx]}"
    done
}

cleanup() {
    if [ -n "$WATCHER_PID" ] && kill -0 "$WATCHER_PID" 2>/dev/null; then
        kill "$WATCHER_PID" 2>/dev/null || true
        wait "$WATCHER_PID" 2>/dev/null || true
    fi

    if tmux has-session -t "$SESSION" 2>/dev/null; then
        if [ "$SUCCESS" -eq 1 ] && [ "$KEEP_SESSION_ON_SUCCESS" != "1" ]; then
            tmux kill-session -t "$SESSION" 2>/dev/null || true
        elif [ "$SUCCESS" -ne 1 ] && [ "$KEEP_SESSION_ON_FAILURE" != "1" ]; then
            tmux kill-session -t "$SESSION" 2>/dev/null || true
        fi
    fi
}
trap cleanup EXIT

mkdir -p "$REPORT_DIR"
mkdir -p "$SMOKE_WORK_DIR"
mkdir -p "$SMOKE_VERIFY_DIR"

cat > "$SMOKE_WORK_NOTE" <<EOF
## 변경 파일
- 없음

## 사용 skill
- 없음

## 변경 이유
- workspace-local live 3-agent arbitration smoke용 synthetic work note입니다.

## 핵심 변경
- Gemini arbitration lane이 읽을 최소 smoke context만 제공합니다.

## 검증
- 없음

## 남은 리스크
- smoke-only note이며 project canonical truth가 아닙니다.
EOF

cat > "$SMOKE_VERIFY_NOTE" <<EOF
## 변경 파일
- 없음

## 사용 skill
- 없음

## 변경 이유
- workspace-local live 3-agent arbitration smoke용 synthetic verify note입니다.

## 핵심 변경
- Codex follow-up이 읽을 최소 smoke verification context만 제공합니다.

## 검증
- 없음

## 남은 리스크
- smoke-only note이며 project canonical truth가 아닙니다.
EOF

cat > "$GEMINI_REQUEST" <<EOF
STATUS: request_open
CONTROL_SEQ: 1

This is a controlled workspace-local live arbitration smoke.

Candidates:
- RECOMMEND: implement live-arbitration-smoke-slice
- RECOMMEND: needs_operator smoke-only fallback

Rules:
- prefer the exact implement recommendation for this smoke
- do not explore a real product axis
- do not widen scope beyond this smoke-only slice
EOF

REQUEST_SEQ="$(read_header_value "$GEMINI_REQUEST" "CONTROL_SEQ" 2>/dev/null || true)"
if ! [[ "$REQUEST_SEQ" =~ ^[0-9]+$ ]]; then
    echo "Seeded gemini_request.md missing valid CONTROL_SEQ: $GEMINI_REQUEST" >&2
    cat "$GEMINI_REQUEST" >&2 || true
    exit 1
fi
EXPECTED_NEXT_SEQ="$((REQUEST_SEQ + 1))"

if tmux has-session -t "$SESSION" 2>/dev/null; then
    tmux kill-session -t "$SESSION"
fi

tmux new-session -d -s "$SESSION" -c "$PROJECT_ROOT" "bash --noprofile --norc"
CLAUDE_PANE="$(tmux display-message -t "$SESSION:0.0" -p '#{pane_id}')"
CODEX_PANE="$(tmux split-window -P -F '#{pane_id}' -h -t "$SESSION:0" -c "$PROJECT_ROOT" "codex --ask-for-approval never --disable apps")"
GEMINI_PANE="$(tmux split-window -P -F '#{pane_id}' -v -t "$CODEX_PANE" -c "$PROJECT_ROOT" "gemini --yolo")"

wait_for_cli_ready "$CODEX_PANE" 25 || true
wait_for_cli_ready "$GEMINI_PANE" 25 || true

VERIFY_PROMPT="ROLE: codex_verify\nSTATE: verify_pending\nNEXT_CONTROL_SEQ: {next_control_seq}\nLATEST_WORK: {latest_work_path}\nLATEST_VERIFY: {latest_verify_path}\nREAD_FIRST:\n- AGENTS.md\n- work/README.md\n- verify/README.md\n- .pipeline/README.md\nOUTPUTS:\n- /verify verification note if needed\n- ${BASE_REL}/claude_handoff.md for STATUS: implement + CONTROL_SEQ: {next_control_seq}\n- ${BASE_REL}/gemini_request.md when Codex cannot narrow after tie-break + CONTROL_SEQ: {next_control_seq}\n- ${BASE_REL}/operator_request.md only when Gemini still cannot resolve it + CONTROL_SEQ: {next_control_seq}\nRULES:\n- latest /work first, then same-day latest /verify if any\n- never route needs_operator to Claude\n- when writing a control slot, put CONTROL_SEQ immediately after STATUS and use exactly {next_control_seq}\n- if you write ${BASE_REL}/operator_request.md, keep STATUS/CONTROL_SEQ in the first 12 lines and include REASON_CODE, OPERATOR_POLICY, DECISION_CLASS, DECISION_REQUIRED, BASED_ON_WORK, and BASED_ON_VERIFY near the top\n- keep one exact next slice or one exact operator decision only"
CLAUDE_PROMPT="ROLE: claude_implement\nSTATE: implement\nHANDOFF: {active_handoff_path}\nHANDOFF_SHA: {active_handoff_sha}\nREAD_FIRST:\n- CLAUDE.md\n- {active_handoff_path}\nRULES:\n- implement only the bounded slice from the handoff\n- do not ask the operator to choose among options\n- do not self-select the next slice\n- do not write or update ${BASE_REL}/gemini_request.md or ${BASE_REL}/operator_request.md\n- if the handoff is blocked or not actionable, emit the exact sentinel below and stop\nBLOCKED_SENTINEL:\nSTATUS: implement_blocked\nBLOCK_REASON: <short_reason>\nBLOCK_REASON_CODE: <reason_code>\nREQUEST: codex_triage\nESCALATION_CLASS: codex_triage\nHANDOFF: {active_handoff_path}\nHANDOFF_SHA: {active_handoff_sha}\nBLOCK_ID: {active_handoff_sha}:<short_reason>"
GEMINI_PROMPT="ROLE: gemini_arbitrate\nSTATE: codex_needs_tiebreak\nNEXT_CONTROL_SEQ: {next_control_seq}\nREQUEST_FILE: ${GEMINI_REQUEST}\nThis is a controlled smoke only.\nThe request file already contains the exact smoke recommendation.\nDo not inspect unrelated repo files.\nWrite exactly two files now using edit/write tools only:\n- advisory log: ${REPORT_DIR}/2026-04-03-live-arbitration-smoke.md\n- recommendation slot: ${GEMINI_ADVICE} with STATUS: advice_ready and CONTROL_SEQ: {next_control_seq}\nRecommendation content should choose the smoke-only implement recommendation from ${GEMINI_REQUEST}.\nDo not use shell heredoc, shell redirection, cat > file, or printf > file.\nDo not modify any other repo files.\nWrite CONTROL_SEQ immediately after STATUS using exactly {next_control_seq}.\nKeep both outputs short and exact."
CODEX_FOLLOWUP_PROMPT="ROLE: codex_followup\nSTATE: gemini_advice_ready\nREQUEST: ${GEMINI_REQUEST}\nADVICE: ${GEMINI_ADVICE}\nThis is a controlled smoke follow-up only.\nDo not inspect unrelated repo files.\nWrite exactly one final control slot now:\n- ${CLAUDE_HANDOFF} for STATUS: implement + CONTROL_SEQ: ${EXPECTED_NEXT_SEQ}\n- or ${OPERATOR_REQUEST} for STATUS: needs_operator + CONTROL_SEQ: ${EXPECTED_NEXT_SEQ}\nPrefer the smoke-only implement recommendation when present.\nDo not use shell heredoc, shell redirection, cat > file, or printf > file.\nWhen writing the final control slot, put CONTROL_SEQ immediately after STATUS and use exactly ${EXPECTED_NEXT_SEQ}.\nIf you write ${OPERATOR_REQUEST}, keep STATUS/CONTROL_SEQ in the first 12 lines and include REASON_CODE, OPERATOR_POLICY, DECISION_CLASS, DECISION_REQUIRED, BASED_ON_WORK, and BASED_ON_VERIFY near the top."

python3 "$SCRIPT_DIR/watcher_core.py" \
    --watch-dir "$BASE_DIR/work" \
    --base-dir "$BASE_DIR" \
    --repo-root "$PROJECT_ROOT" \
    --verify-pane-target "$CODEX_PANE" \
    --claude-pane-target "$CLAUDE_PANE" \
    --gemini-pane-target "$GEMINI_PANE" \
    --verify-prompt "$VERIFY_PROMPT" \
    --claude-prompt "$CLAUDE_PROMPT" \
    --gemini-prompt "$GEMINI_PROMPT" \
    --codex-followup-prompt "$CODEX_FOLLOWUP_PROMPT" \
    --startup-grace "$STARTUP_GRACE" \
    --lease-ttl 600 \
    > "$WATCHER_LOG" 2>&1 &
WATCHER_PID="$!"

if ! wait_for_status "$GEMINI_ADVICE" "advice_ready" "$TIMEOUT_SEC"; then
    echo "Gemini advice slot timed out: $GEMINI_ADVICE" >&2
    echo "watcher log: $WATCHER_LOG" >&2
    tmux capture-pane -pt "$GEMINI_PANE" -S -80 >&2 || true
    exit 1
fi

ADVICE_SEQ="$(read_header_value "$GEMINI_ADVICE" "CONTROL_SEQ" 2>/dev/null || true)"
if [ "$ADVICE_SEQ" != "$EXPECTED_NEXT_SEQ" ]; then
    echo "Gemini advice CONTROL_SEQ mismatch: expected $EXPECTED_NEXT_SEQ got ${ADVICE_SEQ:-missing}" >&2
    echo "watcher log: $WATCHER_LOG" >&2
    cat "$GEMINI_ADVICE" >&2 || true
    exit 1
fi

if ! find "$REPORT_DIR" -maxdepth 1 -type f -name '*.md' | grep -q .; then
    echo "Gemini report log missing under $REPORT_DIR" >&2
    echo "watcher log: $WATCHER_LOG" >&2
    exit 1
fi

if ! wait_for_final_slot "$TIMEOUT_SEC"; then
    echo "Codex follow-up timed out: expected claude_handoff or operator_request" >&2
    echo "watcher log: $WATCHER_LOG" >&2
    tmux capture-pane -pt "$CODEX_PANE" -S -80 >&2 || true
    exit 1
fi

HANDOFF_STATUS="$(read_status "$CLAUDE_HANDOFF" 2>/dev/null || true)"
OPERATOR_STATUS="$(read_status "$OPERATOR_REQUEST" 2>/dev/null || true)"
FINAL_SLOT=""
if [ "$HANDOFF_STATUS" = "implement" ] && [ "$OPERATOR_STATUS" = "needs_operator" ]; then
    echo "Unexpected dual final slots: both claude_handoff and operator_request are pending" >&2
    cat "$CLAUDE_HANDOFF" >&2 || true
    cat "$OPERATOR_REQUEST" >&2 || true
    exit 1
elif [ "$HANDOFF_STATUS" = "implement" ]; then
    FINAL_SLOT="$CLAUDE_HANDOFF"
elif [ "$OPERATOR_STATUS" = "needs_operator" ]; then
    FINAL_SLOT="$OPERATOR_REQUEST"
else
    echo "Final slot status missing after wait_for_final_slot" >&2
    echo "watcher log: $WATCHER_LOG" >&2
    exit 1
fi

FINAL_SEQ="$(read_header_value "$FINAL_SLOT" "CONTROL_SEQ" 2>/dev/null || true)"
if [ "$FINAL_SEQ" != "$EXPECTED_NEXT_SEQ" ]; then
    echo "Final control slot CONTROL_SEQ mismatch: expected $EXPECTED_NEXT_SEQ got ${FINAL_SEQ:-missing}" >&2
    echo "final slot: $FINAL_SLOT" >&2
    cat "$FINAL_SLOT" >&2 || true
    exit 1
fi

SUCCESS=1
prune_old_smoke_dirs "$KEEP_RECENT_SMOKES"
echo "3-agent arbitration smoke OK"
echo "base_dir: $BASE_DIR"
echo "watcher_log: $WATCHER_LOG"
echo "gemini_advice: $GEMINI_ADVICE"
echo "claude_handoff: $CLAUDE_HANDOFF"
echo "operator_request: $OPERATOR_REQUEST"
echo "report_dir: $REPORT_DIR"
echo "kept_recent_smokes: $KEEP_RECENT_SMOKES"
