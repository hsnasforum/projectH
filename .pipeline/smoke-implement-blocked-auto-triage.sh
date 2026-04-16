#!/bin/bash
set -euo pipefail

PROJECT_ROOT="${1:-$(pwd)}"
PROJECT_ROOT="$(cd "$PROJECT_ROOT" && pwd)"
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
SESSION="${PIPELINE_BLOCKED_SMOKE_SESSION:-ai-pipeline-blocked-smoke}"
STARTUP_GRACE="${PIPELINE_BLOCKED_SMOKE_STARTUP_GRACE:-3}"
TIMEOUT_SEC="${PIPELINE_BLOCKED_SMOKE_TIMEOUT:-60}"
KEEP_SESSION_ON_FAILURE="${PIPELINE_BLOCKED_SMOKE_KEEP_SESSION_ON_FAILURE:-1}"
KEEP_SESSION_ON_SUCCESS="${PIPELINE_BLOCKED_SMOKE_KEEP_SESSION_ON_SUCCESS:-0}"
KEEP_RECENT_SMOKES="${PIPELINE_BLOCKED_SMOKE_KEEP_RECENT:-3}"

BASE_DIR="$(mktemp -d "$PROJECT_ROOT/.pipeline/live-blocked-smoke-XXXXXX")"
BASE_REL="${BASE_DIR#$PROJECT_ROOT/}"
WATCHER_LOG="$BASE_DIR/watcher.log"
RAW_LOG="$BASE_DIR/logs/experimental/raw.jsonl"
CLAUDE_HANDOFF="$BASE_DIR/claude_handoff.md"
GEMINI_REQUEST="$BASE_DIR/gemini_request.md"
GEMINI_ADVICE="$BASE_DIR/gemini_advice.md"
OPERATOR_REQUEST="$BASE_DIR/operator_request.md"
SMOKE_WORK_DIR="$BASE_DIR/work"
CLAUDE_SHIM="$BASE_DIR/claude_smoke_lane.py"
CODEX_SHIM="$BASE_DIR/codex_smoke_lane.py"
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

read_header_value() {
    local path="$1"
    local key="$2"
    if [ ! -f "$path" ]; then
        return 1
    fi
    awk -F':' -v key="$key" '$1 == key {sub(/^[[:space:]]+/, "", $2); print $2; exit}' "$path"
}

wait_for_header_value() {
    local path="$1"
    local key="$2"
    local expected="$3"
    local timeout_sec="$4"
    local started_at
    local current

    started_at="$(date +%s)"
    while true; do
        current="$(read_header_value "$path" "$key" 2>/dev/null || true)"
        if [ "$current" = "$expected" ]; then
            return 0
        fi
        if [ $(( $(date +%s) - started_at )) -ge "$timeout_sec" ]; then
            return 1
        fi
        sleep 1
    done
}

wait_for_log_contains() {
    local path="$1"
    local pattern="$2"
    local timeout_sec="$3"
    local started_at

    started_at="$(date +%s)"
    while true; do
        if [ -f "$path" ] && grep -Fq "$pattern" "$path"; then
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
    mapfile -t dirs < <(find "$smoke_root" -maxdepth 1 -mindepth 1 -type d -name 'live-blocked-smoke-*' -printf '%T@ %p\n' | sort -nr | awk '{print $2}')
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

mkdir -p "$SMOKE_WORK_DIR"

cat > "$CLAUDE_HANDOFF" <<EOF
STATUS: implement
CONTROL_SEQ: 1

Next slice: \`blocked smoke initial handoff\`

This is a deterministic watcher-path smoke handoff.
EOF

cat > "$CLAUDE_SHIM" <<'PY'
#!/usr/bin/env python3
import sys

from pipeline_runtime.control_writers import render_implement_blocked

sentinel_sent = False
handoff = ""
handoff_sha = ""


def prompt() -> None:
    sys.stdout.write(">\n")
    sys.stdout.flush()


prompt()
for raw in sys.stdin:
    line = raw.rstrip("\n")
    stripped = line.strip()
    if not stripped:
        continue
    if stripped.startswith("HANDOFF: "):
        handoff = stripped.split(":", 1)[1].strip()
        continue
    if stripped.startswith("HANDOFF_SHA: "):
        handoff_sha = stripped.split(":", 1)[1].strip()
        continue
    if stripped.startswith("BLOCK_ID: ") and not sentinel_sent and handoff and handoff_sha:
        sys.stdout.write(
            render_implement_blocked(
                block_reason="smoke_handoff_blocked",
                block_reason_code="codex_triage_only",
                request="codex_triage",
                escalation_class="codex_triage",
                handoff=handoff,
                handoff_sha=handoff_sha,
                block_id=f"{handoff_sha}:smoke_handoff_blocked",
            )
        )
        sys.stdout.flush()
        sentinel_sent = True
        prompt()
        continue
    if stripped.startswith("ROLE: claude_implement") and sentinel_sent:
        sys.stdout.write("Claude smoke resumed after new handoff\n")
        sys.stdout.flush()
        prompt()
PY
chmod +x "$CLAUDE_SHIM"

cat > "$CODEX_SHIM" <<'PY'
#!/usr/bin/env python3
import os
import sys
from pathlib import Path

role = ""
handoff = ""
next_control_seq = "2"
written = False


def prompt() -> None:
    sys.stdout.write(">\n")
    sys.stdout.flush()


prompt()
for raw in sys.stdin:
    line = raw.rstrip("\n")
    stripped = line.strip()
    if not stripped:
        continue
    if stripped.startswith("ROLE: "):
        role = stripped.split(":", 1)[1].strip()
        continue
    if stripped.startswith("HANDOFF: "):
        handoff = stripped.split(":", 1)[1].strip()
        continue
    if stripped.startswith("NEXT_CONTROL_SEQ: "):
        next_control_seq = stripped.split(":", 1)[1].strip() or "2"
        continue
    if stripped.startswith("BLOCK_ID: ") and role == "codex_blocked_triage" and handoff and not written:
        target = Path(handoff)
        if not target.is_absolute():
            target = Path(os.getcwd()) / target
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(
            "STATUS: implement\n"
            f"CONTROL_SEQ: {next_control_seq}\n\n"
            "Next slice: `blocked smoke recovered handoff`\n\n"
            "This handoff was written by the deterministic blocked-triage smoke lane.\n",
            encoding="utf-8",
        )
        sys.stdout.write("• Working smoke blocked triage\n")
        sys.stdout.write(f"• Wrote {target}\n")
        sys.stdout.flush()
        written = True
        prompt()
PY
chmod +x "$CODEX_SHIM"

if tmux has-session -t "$SESSION" 2>/dev/null; then
    tmux kill-session -t "$SESSION"
fi

tmux new-session -d -s "$SESSION" -c "$PROJECT_ROOT" "python3 -u \"$CLAUDE_SHIM\""
CLAUDE_PANE="$(tmux display-message -t "$SESSION:0.0" -p '#{pane_id}')"
CODEX_PANE="$(tmux split-window -P -F '#{pane_id}' -h -t "$SESSION:0" -c "$PROJECT_ROOT" "python3 -u \"$CODEX_SHIM\"")"
GEMINI_PANE="$(tmux split-window -P -F '#{pane_id}' -v -t "$CODEX_PANE" -c "$PROJECT_ROOT" "bash --noprofile --norc")"

wait_for_cli_ready "$CLAUDE_PANE" 20 || true
wait_for_cli_ready "$CODEX_PANE" 20 || true
wait_for_cli_ready "$GEMINI_PANE" 20 || true

python3 "$SCRIPT_DIR/watcher_core.py" \
    --watch-dir "$SMOKE_WORK_DIR" \
    --base-dir "$BASE_DIR" \
    --repo-root "$PROJECT_ROOT" \
    --verify-pane-target "$CODEX_PANE" \
    --claude-pane-target "$CLAUDE_PANE" \
    --gemini-pane-target "$GEMINI_PANE" \
    --startup-grace "$STARTUP_GRACE" \
    --lease-ttl 60 \
    > "$WATCHER_LOG" 2>&1 &
WATCHER_PID="$!"

if ! wait_for_log_contains "$RAW_LOG" "\"event\": \"codex_blocked_triage_notify\"" "$TIMEOUT_SEC"; then
    echo "Blocked triage notify event timed out" >&2
    echo "watcher log: $WATCHER_LOG" >&2
    tmux capture-pane -pt "$CLAUDE_PANE" -S -80 >&2 || true
    tmux capture-pane -pt "$CODEX_PANE" -S -80 >&2 || true
    exit 1
fi

if ! wait_for_header_value "$CLAUDE_HANDOFF" "CONTROL_SEQ" "2" "$TIMEOUT_SEC"; then
    echo "Recovered handoff CONTROL_SEQ timed out: $CLAUDE_HANDOFF" >&2
    echo "watcher log: $WATCHER_LOG" >&2
    cat "$CLAUDE_HANDOFF" >&2 || true
    exit 1
fi

if ! wait_for_log_contains "$RAW_LOG" "\"reason\": \"claude_handoff_updated\"" "$TIMEOUT_SEC"; then
    echo "Claude re-notify after blocked triage timed out" >&2
    echo "watcher log: $WATCHER_LOG" >&2
    cat "$RAW_LOG" >&2 || true
    exit 1
fi

if [ -f "$OPERATOR_REQUEST" ]; then
    echo "operator_request.md should not be opened in blocked auto-triage smoke" >&2
    cat "$OPERATOR_REQUEST" >&2 || true
    exit 1
fi

if [ -f "$GEMINI_REQUEST" ] || [ -f "$GEMINI_ADVICE" ]; then
    echo "Gemini control slots should stay unopened in blocked auto-triage smoke" >&2
    ls -l "$GEMINI_REQUEST" "$GEMINI_ADVICE" 2>/dev/null >&2 || true
    exit 1
fi

SUCCESS=1
prune_old_smoke_dirs "$KEEP_RECENT_SMOKES"
echo "implement_blocked auto-triage smoke OK"
echo "base_dir: $BASE_DIR"
echo "watcher_log: $WATCHER_LOG"
echo "raw_log: $RAW_LOG"
echo "claude_handoff: $CLAUDE_HANDOFF"
echo "kept_recent_smokes: $KEEP_RECENT_SMOKES"
