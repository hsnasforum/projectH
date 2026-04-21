#!/bin/bash
set -euo pipefail

PROJECT_ROOT="${1:-$(pwd)}"
PROJECT_ROOT="$(cd "$PROJECT_ROOT" && pwd)"
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
PIPELINE_LIB_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
# shellcheck disable=SC1091
. "$PIPELINE_LIB_DIR/smoke-cleanup-lib.sh"
SMOKE_TOPOLOGY="${PIPELINE_SMOKE_TOPOLOGY:-swapped}"
SESSION="${PIPELINE_SMOKE_SESSION:-ai-pipeline-smoke-$SMOKE_TOPOLOGY}"
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
CLAUDE_BIN=""
CODEX_BIN=""
GEMINI_BIN=""

find_cli_bin() {
    local name="$1"
    local found

    found="$(command -v "$name" 2>/dev/null || true)"
    if [ -n "$found" ]; then
        printf '%s\n' "$found"
        return 0
    fi

    if [ -s "$HOME/.nvm/nvm.sh" ]; then
        # shellcheck disable=SC1090
        . "$HOME/.nvm/nvm.sh" 2>/dev/null
        found="$(command -v "$name" 2>/dev/null || true)"
        if [ -n "$found" ]; then
            printf '%s\n' "$found"
            return 0
        fi
    fi

    for dir in "$HOME/.nvm/versions/node"/*/bin "$HOME/.local/bin" "/usr/local/bin"; do
        if [ -x "$dir/$name" ]; then
            printf '%s\n' "$dir/$name"
            return 0
        fi
    done

    return 1
}

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

    # Delegate to the shared canonical caller in smoke-cleanup-lib.sh so the
    # live-arb auto-prune contract (protect_tracked=0 on
    # `.pipeline/live-arb-smoke-*`) is covered by focused regressions in
    # tests/test_pipeline_smoke_cleanup.py without sourcing this tmux script.
    prune_live_arb_smoke_dirs "$PROJECT_ROOT" "$keep_recent"
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
- verify/handoff owner가 읽을 최소 smoke verification context만 제공합니다.

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

resolve_read_first_doc() {
    local owner="$1"
    case "$owner" in
        Claude) printf '%s\n' "CLAUDE.md" ;;
        Gemini) printf '%s\n' "GEMINI.md" ;;
        *) printf '%s\n' "AGENTS.md" ;;
    esac
}

eval "$(
PROJECT_ROOT="$PROJECT_ROOT" \
BASE_DIR="$BASE_DIR" \
SMOKE_TOPOLOGY="$SMOKE_TOPOLOGY" \
PIPELINE_SMOKE_ROLE_BINDINGS_JSON="${PIPELINE_SMOKE_ROLE_BINDINGS_JSON:-}" \
python3 - <<'PY'
import json
import os
from pathlib import Path

from pipeline_runtime.lane_catalog import (
    build_agent_profile_payload,
    default_role_bindings,
    legacy_role_bindings,
)

project_root = Path(os.environ["PROJECT_ROOT"])
base_dir = Path(os.environ["BASE_DIR"])
topology = str(os.environ.get("SMOKE_TOPOLOGY") or "swapped").strip().lower()
bindings_override_raw = str(os.environ.get("PIPELINE_SMOKE_ROLE_BINDINGS_JSON") or "").strip()
profile_path = project_root / ".pipeline" / "config" / "agent_profile.json"

bindings = default_role_bindings()
if topology == "legacy":
    bindings = legacy_role_bindings()
elif topology == "active":
    try:
        payload = json.loads(profile_path.read_text(encoding="utf-8"))
    except Exception:
        payload = {}
    raw = dict(payload.get("role_bindings") or {})
    for key in bindings:
        value = str(raw.get(key) or "").strip()
        if value:
            bindings[key] = value
elif topology != "swapped":
    raise SystemExit(f"Unsupported PIPELINE_SMOKE_TOPOLOGY={topology}")

if bindings_override_raw:
    override_payload = json.loads(bindings_override_raw)
    if not isinstance(override_payload, dict):
        raise SystemExit("PIPELINE_SMOKE_ROLE_BINDINGS_JSON must be a JSON object")
    for key in bindings:
        value = str(override_payload.get(key) or "").strip()
        if value:
            bindings[key] = value

smoke_profile_path = base_dir / ".pipeline" / "config" / "agent_profile.json"
smoke_profile_path.parent.mkdir(parents=True, exist_ok=True)
smoke_payload = build_agent_profile_payload(
    selected_agents=None,
    role_bindings=bindings,
    advisory_enabled=True,
    operator_stop_enabled=True,
    session_arbitration_enabled=True,
    single_agent_mode=False,
    self_verify_allowed=False,
    self_advisory_allowed=False,
)
smoke_profile_path.write_text(
    json.dumps(smoke_payload, ensure_ascii=False, indent=2),
    encoding="utf-8",
)
print(f'SMOKE_TOPOLOGY_RESOLVED={json.dumps(topology)}')
print(f'SMOKE_PROFILE_PATH={json.dumps(str(smoke_profile_path))}')
for key, value in bindings.items():
    print(f'{key.upper()}_OWNER={json.dumps(value)}')
PY
)"

IMPLEMENT_READ_FIRST="$(resolve_read_first_doc "$IMPLEMENT_OWNER")"
VERIFY_READ_FIRST="$(resolve_read_first_doc "$VERIFY_OWNER")"
ADVISORY_READ_FIRST="$(resolve_read_first_doc "$ADVISORY_OWNER")"
CLAUDE_BIN="$(find_cli_bin claude || true)"
CODEX_BIN="$(find_cli_bin codex || true)"
GEMINI_BIN="$(find_cli_bin gemini || true)"

if [ -z "$CLAUDE_BIN" ] || [ -z "$CODEX_BIN" ] || [ -z "$GEMINI_BIN" ]; then
    echo "Missing required CLI binary for live arbitration smoke." >&2
    echo "claude=${CLAUDE_BIN:-missing}" >&2
    echo "codex=${CODEX_BIN:-missing}" >&2
    echo "gemini=${GEMINI_BIN:-missing}" >&2
    exit 1
fi

if tmux has-session -t "$SESSION" 2>/dev/null; then
    tmux kill-session -t "$SESSION"
fi

tmux new-session -d -s "$SESSION" -c "$PROJECT_ROOT" "exec \"$CLAUDE_BIN\" --dangerously-skip-permissions"
CLAUDE_PANE="$(tmux display-message -t "$SESSION:0.0" -p '#{pane_id}')"
CODEX_PANE="$(tmux split-window -P -F '#{pane_id}' -h -t "$SESSION:0" -c "$PROJECT_ROOT" "exec \"$CODEX_BIN\" --ask-for-approval never --disable apps")"
GEMINI_PANE="$(tmux split-window -P -F '#{pane_id}' -v -t "$CODEX_PANE" -c "$PROJECT_ROOT" "exec \"$GEMINI_BIN\" --approval-mode auto_edit")"

wait_for_cli_ready "$CLAUDE_PANE" 25 || true
wait_for_cli_ready "$CODEX_PANE" 25 || true
wait_for_cli_ready "$GEMINI_PANE" 25 || true

VERIFY_PROMPT="ROLE: verify\nOWNER: ${VERIFY_OWNER}\nSTATE: verify_pending\nNEXT_CONTROL_SEQ: {next_control_seq}\nLATEST_WORK: {latest_work_path}\nLATEST_VERIFY: {latest_verify_path}\nREAD_FIRST:\n- ${VERIFY_READ_FIRST}\n- work/README.md\n- verify/README.md\n- .pipeline/README.md\nOUTPUTS:\n- /verify verification note if needed\n- ${BASE_REL}/claude_handoff.md for STATUS: implement + CONTROL_SEQ: {next_control_seq}\n- ${BASE_REL}/gemini_request.md when verify/handoff owner cannot narrow after tie-break + CONTROL_SEQ: {next_control_seq}\n- ${BASE_REL}/operator_request.md only when advisory still cannot resolve it + CONTROL_SEQ: {next_control_seq}\nRULES:\n- latest /work first, then same-day latest /verify if any\n- keep one exact next slice or one exact operator decision only\n- when writing a control slot, put CONTROL_SEQ immediately after STATUS and use exactly {next_control_seq}\n- if you write ${BASE_REL}/operator_request.md, keep STATUS/CONTROL_SEQ in the first 12 lines and include REASON_CODE, OPERATOR_POLICY, DECISION_CLASS, DECISION_REQUIRED, BASED_ON_WORK, and BASED_ON_VERIFY near the top"
IMPLEMENT_PROMPT="ROLE: implement\nOWNER: ${IMPLEMENT_OWNER}\nSTATE: implement\nHANDOFF: {active_handoff_path}\nHANDOFF_SHA: {active_handoff_sha}\nREAD_FIRST:\n- ${IMPLEMENT_READ_FIRST}\n- {active_handoff_path}\nRULES:\n- implement only the bounded slice from the handoff\n- do not ask the operator to choose among options\n- do not self-select the next slice\n- do not write or update ${BASE_REL}/gemini_request.md or ${BASE_REL}/operator_request.md\n- if the handoff is blocked or not actionable, emit the exact sentinel below and stop\nBLOCKED_SENTINEL:\nSTATUS: implement_blocked\nBLOCK_REASON: <short_reason>\nBLOCK_REASON_CODE: <reason_code>\nREQUEST: codex_triage\nESCALATION_CLASS: codex_triage\nHANDOFF: {active_handoff_path}\nHANDOFF_SHA: {active_handoff_sha}\nBLOCK_ID: {active_handoff_sha}:<short_reason>"
ADVISORY_PROMPT="ROLE: advisory\nOWNER: ${ADVISORY_OWNER}\nSTATE: verify_needs_tiebreak\nNEXT_CONTROL_SEQ: {next_control_seq}\nREQUEST_FILE: ${GEMINI_REQUEST}\nThis is a controlled smoke only.\nThe request file already contains the exact smoke recommendation.\nDo not inspect unrelated repo files.\nWrite exactly two files now using edit/write tools only:\n- advisory log: ${REPORT_DIR}/2026-04-03-live-arbitration-smoke.md\n- recommendation slot: ${GEMINI_ADVICE} with STATUS: advice_ready and CONTROL_SEQ: {next_control_seq}\nRecommendation content should choose the smoke-only implement recommendation from ${GEMINI_REQUEST}.\nDo not use shell heredoc, shell redirection, cat > file, or printf > file.\nDo not modify any other repo files.\nWrite CONTROL_SEQ immediately after STATUS using exactly {next_control_seq}.\nKeep both outputs short and exact."
FOLLOWUP_PROMPT="ROLE: followup\nOWNER: ${VERIFY_OWNER}\nSTATE: advisory_ready\nREQUEST: ${GEMINI_REQUEST}\nADVICE: ${GEMINI_ADVICE}\nThis is a controlled smoke follow-up only.\nDo not inspect unrelated repo files.\nWrite exactly one final control slot now:\n- ${CLAUDE_HANDOFF} for STATUS: implement + CONTROL_SEQ: ${EXPECTED_NEXT_SEQ}\n- or ${OPERATOR_REQUEST} for STATUS: needs_operator + CONTROL_SEQ: ${EXPECTED_NEXT_SEQ}\nPrefer the smoke-only implement recommendation when present.\nDo not use shell heredoc, shell redirection, cat > file, or printf > file.\nWhen writing the final control slot, put CONTROL_SEQ immediately after STATUS and use exactly ${EXPECTED_NEXT_SEQ}.\nIf you write ${OPERATOR_REQUEST}, keep STATUS/CONTROL_SEQ in the first 12 lines and include REASON_CODE, OPERATOR_POLICY, DECISION_CLASS, DECISION_REQUIRED, BASED_ON_WORK, and BASED_ON_VERIFY near the top."

python3 "$SCRIPT_DIR/watcher_core.py" \
    --watch-dir "$BASE_DIR/work" \
    --base-dir "$BASE_DIR" \
    --repo-root "$BASE_DIR" \
    --verify-pane-target "$CODEX_PANE" \
    --claude-pane-target "$CLAUDE_PANE" \
    --gemini-pane-target "$GEMINI_PANE" \
    --verify-prompt "$VERIFY_PROMPT" \
    --claude-prompt "$IMPLEMENT_PROMPT" \
    --gemini-prompt "$ADVISORY_PROMPT" \
    --codex-followup-prompt "$FOLLOWUP_PROMPT" \
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
    echo "Verify follow-up timed out: expected claude_handoff or operator_request" >&2
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

if ! python3 "$PROJECT_ROOT/scripts/pipeline_runtime_gate.py" --project-root "$PROJECT_ROOT" --session "$SESSION" check-operator-classification >/dev/null; then
    echo "classification_fallback_detected during 3-agent arbitration smoke" >&2
    echo "watcher log: $WATCHER_LOG" >&2
    cat "$FINAL_SLOT" >&2 || true
    exit 1
fi

SUCCESS=1
prune_old_smoke_dirs "$KEEP_RECENT_SMOKES"
echo "3-agent arbitration smoke OK"
echo "topology: $SMOKE_TOPOLOGY_RESOLVED"
echo "base_dir: $BASE_DIR"
echo "smoke_profile: $SMOKE_PROFILE_PATH"
echo "watcher_log: $WATCHER_LOG"
echo "gemini_advice: $GEMINI_ADVICE"
echo "claude_handoff: $CLAUDE_HANDOFF"
echo "operator_request: $OPERATOR_REQUEST"
echo "report_dir: $REPORT_DIR"
echo "kept_recent_smokes: $KEEP_RECENT_SMOKES"
