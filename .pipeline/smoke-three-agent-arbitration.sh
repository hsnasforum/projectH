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

This is a controlled workspace-local live arbitration smoke.

Candidates:
- RECOMMEND: implement live-arbitration-smoke-slice
- RECOMMEND: needs_operator smoke-only fallback

Rules:
- prefer the exact implement recommendation for this smoke
- do not explore a real product axis
- do not widen scope beyond this smoke-only slice
EOF

if tmux has-session -t "$SESSION" 2>/dev/null; then
    tmux kill-session -t "$SESSION"
fi

tmux new-session -d -s "$SESSION" -c "$PROJECT_ROOT" "bash --noprofile --norc"
CLAUDE_PANE="$(tmux display-message -t "$SESSION:0.0" -p '#{pane_id}')"
CODEX_PANE="$(tmux split-window -P -F '#{pane_id}' -h -t "$SESSION:0" -c "$PROJECT_ROOT" "codex --ask-for-approval never --disable apps")"
GEMINI_PANE="$(tmux split-window -P -F '#{pane_id}' -v -t "$CODEX_PANE" -c "$PROJECT_ROOT" "gemini --approval-mode auto_edit")"

wait_for_cli_ready "$CODEX_PANE" 25 || true
wait_for_cli_ready "$GEMINI_PANE" 25 || true

VERIFY_PROMPT="ROLE: codex_verify\nSTATE: verify_pending\nLATEST_WORK: {latest_work_path}\nLATEST_VERIFY: {latest_verify_path}\nREAD_FIRST:\n- AGENTS.md\n- work/README.md\n- verify/README.md\n- .pipeline/README.md\nOUTPUTS:\n- /verify verification note if needed\n- ${BASE_REL}/claude_handoff.md for STATUS: implement\n- ${BASE_REL}/gemini_request.md when Codex cannot narrow after tie-break\n- ${BASE_REL}/operator_request.md only when Gemini still cannot resolve it\nRULES:\n- latest /work first, then same-day latest /verify if any\n- never route needs_operator to Claude\n- keep one exact next slice or one exact operator decision only"
CLAUDE_PROMPT="ROLE: claude_implement\nSTATE: implement\nHANDOFF: ${BASE_REL}/claude_handoff.md\nREAD_FIRST:\n- CLAUDE.md\n- ${BASE_REL}/claude_handoff.md"
GEMINI_PROMPT="ROLE: gemini_arbitrate\nSTATE: codex_needs_tiebreak\nOpen these files now:\n- @GEMINI.md\n- @${BASE_REL}/gemini_request.md\n- @AGENTS.md\n- {latest_work_mention}\n- {latest_verify_mention}\nThis is a controlled smoke only. If the request names an explicit smoke-only implement recommendation, prefer that exact recommendation and write the files now.\nWrite exactly two files using edit/write tools only:\n- advisory log: ${BASE_REL}/report/gemini/2026-04-03-live-arbitration-smoke.md\n- recommendation slot: ${BASE_REL}/gemini_advice.md\nDo not use shell heredoc, shell redirection, cat > file, or printf > file.\nDo not modify any other repo files.\nKeep the recommendation short and exact."
CODEX_FOLLOWUP_PROMPT="ROLE: codex_followup\nSTATE: gemini_advice_ready\nREQUEST: ${BASE_REL}/gemini_request.md\nADVICE: ${BASE_REL}/gemini_advice.md\nLATEST_WORK: {latest_work_path}\nLATEST_VERIFY: {latest_verify_path}\nREAD_FIRST:\n- AGENTS.md\n- verify/README.md\n- .pipeline/README.md\n- ${BASE_REL}/gemini_request.md\n- ${BASE_REL}/gemini_advice.md"

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
