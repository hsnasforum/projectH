#!/bin/bash
set -euo pipefail

PROJECT_ROOT="${1:-$(pwd)}"
PROJECT_ROOT="$(cd "$PROJECT_ROOT" && pwd)"
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
PIPELINE_LIB_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
# shellcheck disable=SC1091
. "$PIPELINE_LIB_DIR/smoke-cleanup-lib.sh"
SESSION="${PIPELINE_BLOCKED_SMOKE_SESSION:-ai-pipeline-blocked-smoke}"
STARTUP_GRACE="${PIPELINE_BLOCKED_SMOKE_STARTUP_GRACE:-3}"
TIMEOUT_SEC="${PIPELINE_BLOCKED_SMOKE_TIMEOUT:-60}"
KEEP_SESSION_ON_FAILURE="${PIPELINE_BLOCKED_SMOKE_KEEP_SESSION_ON_FAILURE:-1}"
KEEP_SESSION_ON_SUCCESS="${PIPELINE_BLOCKED_SMOKE_KEEP_SESSION_ON_SUCCESS:-0}"
KEEP_RECENT_SMOKES="${PIPELINE_BLOCKED_SMOKE_KEEP_RECENT:-3}"
SUCCESS=0
WATCHER_PID=""
IMPLEMENT_OWNER=""
VERIFY_OWNER=""
CLAUDE_PHYSICAL_PANE=""
CODEX_PHYSICAL_PANE=""
IMPLEMENT_PANE=""
VERIFY_PANE=""

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

    # Delegate to the shared canonical caller in smoke-cleanup-lib.sh so the
    # blocked-smoke auto-prune contract (protect_tracked=1 on
    # `.pipeline/live-blocked-smoke-*`) is covered by focused regressions in
    # tests/test_pipeline_smoke_cleanup.py without sourcing this tmux script.
    prune_blocked_smoke_dirs "$PROJECT_ROOT" "$keep_recent"
}

resolve_role_bound_smoke_owners() {
    PYTHONPATH="$PROJECT_ROOT${PYTHONPATH:+:$PYTHONPATH}" python3 - "$PROJECT_ROOT" <<'PY'
from pathlib import Path
import sys

from pipeline_gui.setup_profile import resolve_project_runtime_adapter

project_root = Path(sys.argv[1]).resolve()
adapter = resolve_project_runtime_adapter(project_root)
resolution_state = str(adapter.get("resolution_state") or "")
messages = [str(item).strip() for item in list(adapter.get("messages") or []) if str(item).strip()]
role_owners = dict(adapter.get("role_owners") or {})
implement = str(role_owners.get("implement") or "").strip()
verify = str(role_owners.get("verify") or "").strip()
allowed = {"Claude", "Codex"}

errors: list[str] = []
if resolution_state != "ready":
    errors.append(f"active profile is not ready ({resolution_state})")
if not implement:
    errors.append("implement owner missing")
elif implement not in allowed:
    errors.append(f"unsupported implement owner: {implement}")
if not verify:
    errors.append("verify owner missing")
elif verify not in allowed:
    errors.append(f"unsupported verify owner: {verify}")
if implement and verify and implement == verify:
    errors.append(f"implement and verify owners must differ ({implement})")

if errors:
    print(
        "blocked auto-triage smoke requires a ready active profile with "
        "distinct Claude/Codex implement+verify owners",
        file=sys.stderr,
    )
    for message in messages:
        print(f"- {message}", file=sys.stderr)
    for error in errors:
        print(f"- {error}", file=sys.stderr)
    raise SystemExit(64)

print(implement)
print(verify)
PY
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

ROLE_OWNER_OUTPUT="$(resolve_role_bound_smoke_owners)" || {
    echo "blocked auto-triage smoke role resolution failed" >&2
    exit 1
}
IMPLEMENT_OWNER="$(printf '%s\n' "$ROLE_OWNER_OUTPUT" | sed -n '1p')"
VERIFY_OWNER="$(printf '%s\n' "$ROLE_OWNER_OUTPUT" | sed -n '2p')"

BASE_DIR="$(mktemp -d "$PROJECT_ROOT/.pipeline/live-blocked-smoke-XXXXXX")"
BASE_REL="${BASE_DIR#$PROJECT_ROOT/}"
WATCHER_LOG="$BASE_DIR/watcher.log"
RAW_LOG="$BASE_DIR/logs/experimental/raw.jsonl"
CLAUDE_HANDOFF="$BASE_DIR/claude_handoff.md"
GEMINI_REQUEST="$BASE_DIR/gemini_request.md"
GEMINI_ADVICE="$BASE_DIR/gemini_advice.md"
OPERATOR_REQUEST="$BASE_DIR/operator_request.md"
SMOKE_WORK_DIR="$BASE_DIR/work"
IMPLEMENT_SHIM="$BASE_DIR/implement_smoke_lane.py"
VERIFY_SHIM="$BASE_DIR/verify_smoke_lane.py"

mkdir -p "$SMOKE_WORK_DIR"

cat > "$CLAUDE_HANDOFF" <<EOF
STATUS: implement
CONTROL_SEQ: 1

Next slice: \`blocked smoke initial handoff\`

This is a deterministic watcher-path smoke handoff.
EOF

cat > "$IMPLEMENT_SHIM" <<'PY'
#!/usr/bin/env python3
import atexit
import sys
import termios

from pipeline_runtime.control_writers import render_implement_blocked

sentinel_sent = False
handoff = ""
handoff_sha = ""
stdin_fd = None
stdin_attrs = None

try:
    stdin_fd = sys.stdin.fileno()
    stdin_attrs = termios.tcgetattr(stdin_fd)
    noecho_attrs = termios.tcgetattr(stdin_fd)
    noecho_attrs[3] &= ~termios.ECHO
    termios.tcsetattr(stdin_fd, termios.TCSANOW, noecho_attrs)
except (termios.error, OSError):
    stdin_fd = None
    stdin_attrs = None


def restore_tty() -> None:
    if stdin_fd is None or stdin_attrs is None:
        return
    try:
        termios.tcsetattr(stdin_fd, termios.TCSANOW, stdin_attrs)
    except (termios.error, OSError):
        pass


atexit.register(restore_tty)


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
        sys.stdout.write("\n• Working smoke implement\n")
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
        continue
    if stripped.startswith("ROLE: implement") and sentinel_sent:
        # Keep the blocked sentinel as the hot tail so watcher settle/detection
        # sees a stable implement_blocked surface instead of an immediately
        # restored prompt.
        continue
PY
chmod +x "$IMPLEMENT_SHIM"

cat > "$VERIFY_SHIM" <<'PY'
#!/usr/bin/env python3
import atexit
import os
import sys
import termios
from pathlib import Path

role = ""
handoff = ""
next_control_seq = "2"
written = False
stdin_fd = None
stdin_attrs = None

try:
    stdin_fd = sys.stdin.fileno()
    stdin_attrs = termios.tcgetattr(stdin_fd)
    noecho_attrs = termios.tcgetattr(stdin_fd)
    noecho_attrs[3] &= ~termios.ECHO
    termios.tcsetattr(stdin_fd, termios.TCSANOW, noecho_attrs)
except (termios.error, OSError):
    stdin_fd = None
    stdin_attrs = None


def restore_tty() -> None:
    if stdin_fd is None or stdin_attrs is None:
        return
    try:
        termios.tcsetattr(stdin_fd, termios.TCSANOW, stdin_attrs)
    except (termios.error, OSError):
        pass


atexit.register(restore_tty)


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
    if stripped.startswith("BLOCK_ID: ") and role in {"codex_blocked_triage", "verify_triage"} and handoff and not written:
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
chmod +x "$VERIFY_SHIM"

if [ "$IMPLEMENT_OWNER" = "Claude" ]; then
    CLAUDE_LANE_CMD="env PYTHONPATH=\"$PROJECT_ROOT${PYTHONPATH:+:$PYTHONPATH}\" python3 -u \"$IMPLEMENT_SHIM\""
    CODEX_LANE_CMD="env PYTHONPATH=\"$PROJECT_ROOT${PYTHONPATH:+:$PYTHONPATH}\" python3 -u \"$VERIFY_SHIM\""
    IMPLEMENT_PHYSICAL_OWNER="Claude"
    VERIFY_PHYSICAL_OWNER="Codex"
else
    CLAUDE_LANE_CMD="env PYTHONPATH=\"$PROJECT_ROOT${PYTHONPATH:+:$PYTHONPATH}\" python3 -u \"$VERIFY_SHIM\""
    CODEX_LANE_CMD="env PYTHONPATH=\"$PROJECT_ROOT${PYTHONPATH:+:$PYTHONPATH}\" python3 -u \"$IMPLEMENT_SHIM\""
    IMPLEMENT_PHYSICAL_OWNER="Codex"
    VERIFY_PHYSICAL_OWNER="Claude"
fi

if tmux has-session -t "$SESSION" 2>/dev/null; then
    tmux kill-session -t "$SESSION"
fi

tmux new-session -d -s "$SESSION" -c "$PROJECT_ROOT" "$CLAUDE_LANE_CMD"
CLAUDE_PHYSICAL_PANE="$(tmux display-message -t "$SESSION:0.0" -p '#{pane_id}')"
CODEX_PHYSICAL_PANE="$(tmux split-window -P -F '#{pane_id}' -h -t "$SESSION:0" -c "$PROJECT_ROOT" "$CODEX_LANE_CMD")"

if [ "$IMPLEMENT_PHYSICAL_OWNER" = "Claude" ]; then
    IMPLEMENT_PANE="$CLAUDE_PHYSICAL_PANE"
    VERIFY_PANE="$CODEX_PHYSICAL_PANE"
else
    IMPLEMENT_PANE="$CODEX_PHYSICAL_PANE"
    VERIFY_PANE="$CLAUDE_PHYSICAL_PANE"
fi

# Keep the implement shim in the taller full-height pane so the visible tmux
# viewport retains the whole implement_blocked sentinel. Shrink the verify pane
# instead when parking the idle Gemini lane.
GEMINI_PANE="$(tmux split-window -P -F '#{pane_id}' -v -l 6 -t "$VERIFY_PANE" -c "$PROJECT_ROOT" "bash --noprofile --norc")"

wait_for_cli_ready "$CLAUDE_PHYSICAL_PANE" 20 || true
wait_for_cli_ready "$CODEX_PHYSICAL_PANE" 20 || true
wait_for_cli_ready "$GEMINI_PANE" 20 || true

python3 "$SCRIPT_DIR/watcher_core.py" \
    --watch-dir "$SMOKE_WORK_DIR" \
    --base-dir "$BASE_DIR" \
    --repo-root "$PROJECT_ROOT" \
    --verify-pane-target "$CODEX_PHYSICAL_PANE" \
    --claude-pane-target "$CLAUDE_PHYSICAL_PANE" \
    --gemini-pane-target "$GEMINI_PANE" \
    --startup-grace "$STARTUP_GRACE" \
    --lease-ttl 60 \
    > "$WATCHER_LOG" 2>&1 &
WATCHER_PID="$!"

if ! wait_for_log_contains "$RAW_LOG" "\"event\": \"verify_blocked_triage_notify\"" "$TIMEOUT_SEC"; then
    if ! wait_for_log_contains "$RAW_LOG" "\"event\": \"codex_blocked_triage_notify\"" "$TIMEOUT_SEC"; then
        echo "Blocked triage notify event timed out" >&2
        echo "watcher log: $WATCHER_LOG" >&2
        tmux capture-pane -pt "$IMPLEMENT_PANE" -S -80 >&2 || true
        tmux capture-pane -pt "$VERIFY_PANE" -S -80 >&2 || true
        exit 1
    fi
fi

if ! wait_for_log_contains "$RAW_LOG" "\"event\": \"implement_notify\"" "$TIMEOUT_SEC"; then
    echo "Implement notify event timed out" >&2
    echo "watcher log: $WATCHER_LOG" >&2
    tmux capture-pane -pt "$IMPLEMENT_PANE" -S -80 >&2 || true
    exit 1
fi

if ! wait_for_header_value "$CLAUDE_HANDOFF" "CONTROL_SEQ" "2" "$TIMEOUT_SEC"; then
    echo "Recovered handoff CONTROL_SEQ timed out: $CLAUDE_HANDOFF" >&2
    echo "watcher log: $WATCHER_LOG" >&2
    cat "$CLAUDE_HANDOFF" >&2 || true
    exit 1
fi

if ! grep -Eq '"event": "claude_handoff_deferred"|"reason": "claude_handoff_updated"' "$RAW_LOG" 2>/dev/null; then
    if ! wait_for_log_contains "$RAW_LOG" "\"event\": \"claude_handoff_deferred\"" "$TIMEOUT_SEC" && \
       ! wait_for_log_contains "$RAW_LOG" "\"reason\": \"claude_handoff_updated\"" "$TIMEOUT_SEC"; then
        echo "Claude handoff transition after blocked triage timed out" >&2
        echo "watcher log: $WATCHER_LOG" >&2
        cat "$RAW_LOG" >&2 || true
        exit 1
    fi
fi

if grep -Eq '"legacy_event"|"legacy_notify_label"' "$RAW_LOG" 2>/dev/null; then
    echo "Legacy alias fields should not appear in blocked auto-triage smoke raw log" >&2
    cat "$RAW_LOG" >&2 || true
    exit 1
fi

if [ ! -f "$CLAUDE_HANDOFF" ]; then
    echo "Recovered handoff missing after blocked triage" >&2
    echo "watcher log: $WATCHER_LOG" >&2
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

if ! python3 "$PROJECT_ROOT/scripts/pipeline_runtime_gate.py" --project-root "$PROJECT_ROOT" --session "$SESSION" check-operator-classification >/dev/null; then
    echo "classification_fallback_detected during blocked auto-triage smoke" >&2
    echo "watcher log: $WATCHER_LOG" >&2
    exit 1
fi

SUCCESS=1
prune_old_smoke_dirs "$KEEP_RECENT_SMOKES"
echo "implement_blocked auto-triage smoke OK"
echo "base_dir: $BASE_DIR"
echo "watcher_log: $WATCHER_LOG"
echo "raw_log: $RAW_LOG"
echo "claude_handoff: $CLAUDE_HANDOFF"
echo "implement_owner: $IMPLEMENT_OWNER"
echo "verify_owner: $VERIFY_OWNER"
echo "kept_recent_smokes: $KEEP_RECENT_SMOKES"
