#!/bin/bash
# ============================================================
# start-pipeline.sh
# 사용법:
#   bash start-pipeline.sh .                     # 기본: experimental
#   bash start-pipeline.sh . --mode baseline     # baseline만
#   bash start-pipeline.sh . --mode experimental # experimental만
#   bash start-pipeline.sh . --mode both         # 둘 다 (비교 불가, 비권장)
#   bash start-pipeline.sh . --mode experimental --no-attach
# ============================================================

PROJECT_ROOT="${1:-$(pwd)}"
MODE="experimental"
NO_ATTACH=0
SESSION=""

shift 2>/dev/null || true  # skip PROJECT_ROOT positional
for arg in "$@"; do
    case $arg in
        baseline|experimental|both) MODE="$arg" ;;
        --no-attach) NO_ATTACH=1 ;;
        --session) :; ;;  # next arg is the value
        --session=*) SESSION="${arg#*=}" ;;
    esac
done
# Handle --session VALUE (two-arg form)
prev=""
for arg in "$@"; do
    if [ "$prev" = "--session" ]; then SESSION="$arg"; fi
    prev="$arg"
done

# Default: project-aware session name
if [ -z "$SESSION" ]; then
    _proj_name="$(basename "$(readlink -f "$PROJECT_ROOT")")"
    _safe_name="$(printf '%s' "$_proj_name" | tr -cd 'A-Za-z0-9_-')"
    SESSION="aip-${_safe_name:-default}"
fi
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
DATA_DIR="$SCRIPT_DIR"
if [ -f "$SCRIPT_DIR/_data/token_collector.py" ]; then
    DATA_DIR="$SCRIPT_DIR/_data"
fi

resolve_data_file() {
    local name="$1"
    if [ -f "$DATA_DIR/$name" ]; then
        printf '%s' "$DATA_DIR/$name"
        return 0
    fi
    printf '%s' "$SCRIPT_DIR/$name"
}

TOKEN_COLLECTOR_PY="$(resolve_data_file token_collector.py)"
WATCHER_CORE_PY="$(resolve_data_file watcher_core.py)"

check_launch_gate() {
    PYTHONPATH="$SCRIPT_DIR${PYTHONPATH:+:$PYTHONPATH}" python3 - "$PROJECT_ROOT" <<'PY'
from pathlib import Path
import sys

from pipeline_gui.setup_profile import (
    join_display_resolver_messages,
    join_resolver_messages,
    resolve_project_active_profile,
)

project = Path(sys.argv[1]).resolve()
resolved = resolve_project_active_profile(project)
controls = dict(resolved.get("controls") or {})
if bool(controls.get("launch_allowed")):
    raise SystemExit(0)
detail = join_resolver_messages(resolved) or "Active profile launch is blocked."
detail = join_display_resolver_messages(resolved) or detail
print(f"Launch blocked: {detail}")
raise SystemExit(1)
PY
}

load_runtime_adapter_env() {
    local exports_text
    exports_text="$(
        PYTHONPATH="$SCRIPT_DIR${PYTHONPATH:+:$PYTHONPATH}" python3 - "$PROJECT_ROOT" <<'PY'
from pathlib import Path
import shlex
import sys

from pipeline_gui.setup_profile import SETUP_AGENT_ORDER, resolve_project_runtime_adapter

adapter = resolve_project_runtime_adapter(Path(sys.argv[1]).resolve())
controls = dict(adapter.get("controls") or {})
enabled = {str(name).strip() for name in list(adapter.get("enabled_lanes") or []) if str(name).strip()}
role_owners = dict(adapter.get("role_owners") or {})
messages = [str(item).strip() for item in list(adapter.get("messages") or []) if str(item).strip()]
order = {name: idx for idx, name in enumerate(SETUP_AGENT_ORDER)}

values = {
    "RUNTIME_SUPPORT_LEVEL": str(adapter.get("support_level") or "blocked"),
    "RUNTIME_ENABLED_LANES": ",".join(sorted(enabled, key=lambda item: order.get(item, len(order)))),
    "RUNTIME_MESSAGES": " | ".join(messages),
    "LANE_CLAUDE_ENABLED": "1" if "Claude" in enabled else "0",
    "LANE_CODEX_ENABLED": "1" if "Codex" in enabled else "0",
    "LANE_GEMINI_ENABLED": "1" if "Gemini" in enabled else "0",
    "ROLE_IMPLEMENT_OWNER": str(role_owners.get("implement") or ""),
    "ROLE_VERIFY_OWNER": str(role_owners.get("verify") or ""),
    "ROLE_ADVISORY_OWNER": str(role_owners.get("advisory") or ""),
    "CTRL_ADVISORY_ENABLED": "1" if controls.get("advisory_enabled") else "0",
    "CTRL_OPERATOR_STOP_ENABLED": "1" if controls.get("operator_stop_enabled") else "0",
    "CTRL_SESSION_ARBITRATION_ENABLED": "1" if controls.get("session_arbitration_enabled") else "0",
}

for key, value in values.items():
    print(f"{key}={shlex.quote(str(value))}")
PY
    )" || return 1
    local tmpfile
    tmpfile="$(mktemp)" || return 1
    printf '%s\n' "$exports_text" > "$tmpfile"
    # shellcheck disable=SC1090
    . "$tmpfile"
    rm -f "$tmpfile"
}

# CLI 경로 탐지 — non-interactive shell에서도 nvm/npm global을 찾을 수 있도록
# 1차: 현재 PATH에서 탐색
# 2차: nvm 로드 후 재시도
# 3차: 알려진 경로 직접 탐색
_find_cli_bin() {
    local name="$1"
    # 1. 현재 PATH
    local found
    found="$(command -v "$name" 2>/dev/null || true)"
    if [ -n "$found" ]; then echo "$found"; return; fi
    # 2. nvm 로드 후 재시도
    if [ -s "$HOME/.nvm/nvm.sh" ]; then
        . "$HOME/.nvm/nvm.sh" 2>/dev/null
        found="$(command -v "$name" 2>/dev/null || true)"
        if [ -n "$found" ]; then echo "$found"; return; fi
    fi
    # 3. 알려진 경로 직접 탐색
    for dir in "$HOME/.nvm/versions/node"/*/bin "$HOME/.local/bin" "/usr/local/bin"; do
        if [ -x "$dir/$name" ]; then echo "$dir/$name"; return; fi
    done
}

CLAUDE_BIN="$(_find_cli_bin claude)"
CODEX_BIN="$(_find_cli_bin codex)"
GEMINI_BIN="$(_find_cli_bin gemini)"

GREEN='\033[0;32m'
CYAN='\033[0;36m'
YELLOW='\033[1;33m'
GRAY='\033[0;37m'
NC='\033[0m'

terminate_repo_watchers() {
    local project_abs
    project_abs="$(readlink -f "$PROJECT_ROOT")"
    local pids pid cmd cwd

    pids="$(pgrep -f 'watcher_core\.py|pipeline-watcher-v3(\-logged)?\.sh' || true)"
    for pid in $pids; do
        cmd="$(tr '\0' ' ' < "/proc/$pid/cmdline" 2>/dev/null || true)"
        cwd="$(readlink -f "/proc/$pid/cwd" 2>/dev/null || true)"
        case "$cmd" in
            *watcher_core.py*|*pipeline-watcher-v3.sh*|*pipeline-watcher-v3-logged.sh*)
                if [ "$cwd" = "$project_abs" ] || printf '%s' "$cmd" | grep -Fq "$project_abs"; then
                    kill "$pid" 2>/dev/null || true
                fi
                ;;
        esac
    done
}

wait_for_cli_ready() {
    local pane_target="$1"
    local lane_name="$2"
    local pane_text

    sleep 1
    pane_text=$(tmux capture-pane -pt "$pane_target" -S -20 2>/dev/null || true)
    if printf '%s\n' "$pane_text" | awk 'NF { print }' | tail -n 12 | grep -Eq '^[[:space:]]*(>|›|❯)([[:space:]].*)?$|[$][[:space:]]*$'; then
        echo -e "${GRAY}  ${lane_name} 준비 완료 (즉시)${NC}"
        return 0
    fi

    echo -e "${GRAY}  ${lane_name} prompt 미확인, watcher readiness에 맡기고 계속 진행${NC}"
}

launch_agent_in_pane() {
    local pane_target="$1"
    local lane_name="$2"
    local cmd_text="$3"

    # tmux respawn-pane은 새 shell을 만들므로 nvm/PATH가 없을 수 있음.
    # nvm을 먼저 source하여 올바른 node가 PATH에 오도록 한다.
    local nvm_prefix=""
    if [ -s "$HOME/.nvm/nvm.sh" ]; then
        nvm_prefix='. "$HOME/.nvm/nvm.sh" 2>/dev/null; '
    fi

    tmux respawn-pane -k -t "$pane_target" -c "$PROJECT_ROOT" "${nvm_prefix}${cmd_text}" >/dev/null 2>&1 || {
        echo -e "${YELLOW}  ${lane_name} pane respawn 실패${NC}"
        return 1
    }
    return 0
}

launch_disabled_lane_in_pane() {
    local pane_target="$1"
    local lane_name="$2"
    local message
    printf -v message "Physical lane %s disabled by active runtime plan; no runtime role is routed here." "$lane_name"
    tmux respawn-pane -k -t "$pane_target" -c "$PROJECT_ROOT" "printf '%s\n' \"$message\"; exec bash" >/dev/null 2>&1 || {
        echo -e "${YELLOW}  ${lane_name} disabled placeholder respawn 실패${NC}"
        return 1
    }
    return 0
}

launch_runtime_lane() {
    local pane_target="$1"
    local lane_name="$2"
    local enabled_flag="$3"
    local cmd_text="$4"

    if [ "$enabled_flag" = "1" ]; then
        launch_agent_in_pane "$pane_target" "$lane_name" "$cmd_text"
        wait_for_cli_ready "$pane_target" "$lane_name"
        return $?
    fi

    launch_disabled_lane_in_pane "$pane_target" "$lane_name"
}

require_agent_bin() {
    local label="$1"
    local path="$2"
    if [ -n "$path" ]; then
        return 0
    fi
    echo -e "${YELLOW}  ${label} 실행 경로를 찾지 못했습니다 (command -v 실패)${NC}"
    return 1
}

write_token_collector_metadata() {
    local pid="$1"
    local pane_id="$2"
    local window_name="$3"
    local launch_mode="$4"
    printf '%s' "$pid" > "$PROJECT_ROOT/.pipeline/usage/collector.pid"
    printf '%s' "$pane_id" > "$PROJECT_ROOT/.pipeline/usage/collector.pane_id"
    printf '%s' "$window_name" > "$PROJECT_ROOT/.pipeline/usage/collector.window_name"
    printf '%s' "$launch_mode" > "$PROJECT_ROOT/.pipeline/usage/collector.launch_mode"
}

spawn_token_collector_tmux() {
    local window_name="usage-collector"
    local token_log_quoted token_cmd_str token_pane token_pid
    token_log_quoted=$(printf '%q' "$PROJECT_ROOT/.pipeline/usage/collector.log")
    TOKEN_CMD=(
        python3 "$TOKEN_COLLECTOR_PY"
        --project-root "$PROJECT_ROOT"
        --db-path "$PROJECT_ROOT/.pipeline/usage/usage.db"
        --poll-interval 3.0
        --daemon
        --since-days 7
    )
    token_cmd_str=$(printf '%q ' "${TOKEN_CMD[@]}")
    if tmux list-windows -t "$SESSION" -F '#{window_name}' 2>/dev/null | grep -Fxq "$window_name"; then
        tmux kill-window -t "$SESSION:$window_name" >/dev/null 2>&1 || true
    fi
    token_pane=$(tmux new-window -d -P -F '#{pane_id}' -t "$SESSION" -n "$window_name" -c "$PROJECT_ROOT" "exec ${token_cmd_str}> $token_log_quoted 2>&1")
    token_pid=$(tmux display-message -p -t "$token_pane" '#{pane_pid}')
    write_token_collector_metadata "$token_pid" "$token_pane" "$window_name" "tmux"
    echo -e "${GRAY}  token collector pane: $token_pane  PID: $token_pid${NC}"
}

echo ""
echo -e "${CYAN}============================================${NC}"
echo -e "${CYAN}  AI Pipeline Launcher  [mode: $MODE]${NC}"
echo -e "${CYAN}============================================${NC}"
echo -e "  프로젝트: $PROJECT_ROOT"
echo ""

if ! check_launch_gate; then
    exit 1
fi

if ! load_runtime_adapter_env; then
    echo -e "${YELLOW}  runtime adapter를 읽지 못했습니다${NC}"
    exit 1
fi

# ------------------------------------------------------------
# 1. 기존 프로세스 정리
# ------------------------------------------------------------
echo -e "${YELLOW}[1/4] 기존 프로세스 정리 중...${NC}"

if tmux has-session -t "$SESSION" 2>/dev/null; then
    tmux kill-session -t "$SESSION"
fi

for pidfile in baseline experimental; do
    pf="$PROJECT_ROOT/.pipeline/$pidfile.pid"
    if [ -f "$pf" ]; then
        kill "$(cat "$pf")" 2>/dev/null
        rm "$pf"
    fi
done

# pid 파일 밖에 남은 repo-local watcher도 함께 정리
terminate_repo_watchers

# ------------------------------------------------------------
# 2. 로그/상태 초기화 (모드별)
# ------------------------------------------------------------
if [ "$MODE" = "baseline" ] || [ "$MODE" = "both" ]; then
    rm -rf "$PROJECT_ROOT/.pipeline/logs/baseline"
    mkdir -p "$PROJECT_ROOT/.pipeline/logs/baseline"
    echo -e "${GRAY}  baseline 로그 초기화${NC}"
fi

if [ "$MODE" = "experimental" ] || [ "$MODE" = "both" ]; then
    # Truncate logs instead of rm -rf (preserves file descriptors)
    mkdir -p "$PROJECT_ROOT/.pipeline/logs/experimental"
    mkdir -p "$PROJECT_ROOT/.pipeline/state"
    mkdir -p "$PROJECT_ROOT/.pipeline/locks"
    mkdir -p "$PROJECT_ROOT/.pipeline/manifests"
    mkdir -p "$PROJECT_ROOT/.pipeline/usage"
    : > "$PROJECT_ROOT/.pipeline/logs/experimental/watcher.log"
    : > "$PROJECT_ROOT/.pipeline/logs/experimental/raw.jsonl"
    : > "$PROJECT_ROOT/.pipeline/logs/experimental/dispatch.jsonl"
    : > "$PROJECT_ROOT/.pipeline/usage/collector.log"
    rm -f "$PROJECT_ROOT/.pipeline/usage/collector.pid" 2>/dev/null
    rm -f "$PROJECT_ROOT/.pipeline/usage/collector.pane_id" 2>/dev/null
    rm -f "$PROJECT_ROOT/.pipeline/usage/collector.window_name" 2>/dev/null
    rm -f "$PROJECT_ROOT/.pipeline/usage/collector.launch_mode" 2>/dev/null
    # Clean state/locks/manifests
    rm -f "$PROJECT_ROOT/.pipeline/state/"* 2>/dev/null
    rm -f "$PROJECT_ROOT/.pipeline/locks/"* 2>/dev/null
    rm -f "$PROJECT_ROOT/.pipeline/manifests/"* 2>/dev/null
    # Clean Zone.Identifier files (WSL artifacts)
    find "$PROJECT_ROOT/.pipeline" -name "*:Zone.Identifier" -delete 2>/dev/null
    echo -e "${GRAY}  experimental 로그/state/locks/manifests 초기화${NC}"
fi

# ------------------------------------------------------------
# 3. tmux 세션 생성
# ------------------------------------------------------------
echo -e "${GREEN}[2/4] tmux 세션 생성 중...${NC}"

tmux new-session -d -s "$SESSION" -c "$PROJECT_ROOT" "bash" >/dev/null 2>&1 || {
    echo -e "${YELLOW}  tmux new-session 실패${NC}"
}
tmux set-option -g destroy-unattached off >/dev/null 2>&1 || true
tmux set-option -g exit-empty off >/dev/null 2>&1 || true

# Session settings
tmux set-option -t "$SESSION" destroy-unattached off
tmux set-option -t "$SESSION" mouse on
tmux set-option -t "$SESSION" status-position bottom
tmux set-option -t "$SESSION" status-style "bg=colour235,fg=colour250"
tmux set-option -t "$SESSION" message-style "bg=colour235,fg=colour250"
tmux set-option -t "$SESSION" mode-style "bg=colour238,fg=colour255"
tmux set-option -t "$SESSION" pane-border-style "fg=colour238"
tmux set-option -t "$SESSION" pane-active-border-style "fg=colour45"
tmux set-option -t "$SESSION" status-left "[#S] "
tmux set-option -t "$SESSION" status-right "#{window_index}:#{window_name} · %H:%M %d-%b-%y"
tmux set-option -t "$SESSION" status-format[0] "#[align=left]#{status-left}#[default] #[align=right]#{status-right}"
tmux set-window-option -t "$SESSION" window-status-format "#I:#W"
tmux set-window-option -t "$SESSION" window-status-current-format "#[bold]#I:#W"
tmux set-option -u -t "$SESSION" status-format[1] 2>/dev/null || true
tmux set-window-option -t "$SESSION:0" remain-on-exit on >/dev/null 2>&1 || true

if [ "$LANE_CLAUDE_ENABLED" = "1" ]; then
    require_agent_bin "Claude" "$CLAUDE_BIN" || exit 1
fi
if [ "$LANE_CODEX_ENABLED" = "1" ]; then
    require_agent_bin "Codex" "$CODEX_BIN" || exit 1
fi
if [ "$LANE_GEMINI_ENABLED" = "1" ]; then
    require_agent_bin "Gemini" "$GEMINI_BIN" || exit 1
fi

# Capture pane IDs for reliable targeting (pane index can shift)
CLAUDE_PANE=$(tmux display-message -t "$SESSION:0.0" -p '#{pane_id}')
CODEX_PANE=$(tmux split-window -P -F '#{pane_id}' -h -t "$CLAUDE_PANE" -c "$PROJECT_ROOT" "bash")
GEMINI_PANE=$(tmux split-window -P -F '#{pane_id}' -h -t "$CODEX_PANE" -c "$PROJECT_ROOT" "bash")
tmux select-layout -t "$SESSION:0" even-horizontal

launch_runtime_lane "$CLAUDE_PANE" "Claude" "$LANE_CLAUDE_ENABLED" "exec \"$CLAUDE_BIN\" --dangerously-skip-permissions"
launch_runtime_lane "$CODEX_PANE" "Codex" "$LANE_CODEX_ENABLED" "exec \"$CODEX_BIN\" --ask-for-approval never --disable apps"
launch_runtime_lane "$GEMINI_PANE" "Gemini" "$LANE_GEMINI_ENABLED" "exec \"$GEMINI_BIN\" --approval-mode auto_edit"

echo -e "${GRAY}  lane panes: Claude=$CLAUDE_PANE  Codex=$CODEX_PANE  Gemini=$GEMINI_PANE${NC}"
echo -e "${GRAY}  tmux scaffold: $SESSION (lane Claude=$CLAUDE_PANE / lane Codex=$CODEX_PANE / lane Gemini=$GEMINI_PANE)${NC}"
echo -e "${GRAY}  runtime roles: implement->${ROLE_IMPLEMENT_OWNER:-—} verify->${ROLE_VERIFY_OWNER:-—} advisory->${ROLE_ADVISORY_OWNER:-—}${NC}"
echo -e "${GRAY}  runtime plan: enabled=${RUNTIME_ENABLED_LANES:-—}${NC}"
echo -e "${GRAY}  runtime controls: advisory=${CTRL_ADVISORY_ENABLED} operator_stop=${CTRL_OPERATOR_STOP_ENABLED} session_arbitration=${CTRL_SESSION_ARBITRATION_ENABLED}${NC}"
sleep 1

# ------------------------------------------------------------
# 4. watcher 실행
# ------------------------------------------------------------
if [ "$MODE" = "baseline" ] || [ "$MODE" = "both" ]; then
    echo -e "${GREEN}[3/4] baseline watcher 시작 중...${NC}"
    BASELINE_LOG_QUOTED=$(printf '%q' "$PROJECT_ROOT/.pipeline/logs/baseline/watcher.log")
    BASELINE_CMD=$(printf '%q ' bash "$SCRIPT_DIR/pipeline-watcher-v3-logged.sh" "$PROJECT_ROOT")
    BASELINE_WATCHER_PANE=$(tmux new-window -d -P -F '#{pane_id}' -t "$SESSION" -n watcher-baseline -c "$PROJECT_ROOT" "exec ${BASELINE_CMD}> $BASELINE_LOG_QUOTED 2>&1")
    tmux display-message -p -t "$BASELINE_WATCHER_PANE" '#{pane_pid}' > "$PROJECT_ROOT/.pipeline/baseline.pid"
    echo -e "${GRAY}  baseline pane: $BASELINE_WATCHER_PANE  PID: $(cat "$PROJECT_ROOT/.pipeline/baseline.pid")${NC}"
else
    echo -e "${GRAY}[3/4] baseline 건너뜀${NC}"
fi

if [ "$MODE" = "experimental" ] || [ "$MODE" = "both" ]; then
    echo -e "${GREEN}[4/4] experimental watcher 시작 중...${NC}"
    VERIFY_PROMPT="ROLE: verify\nROLE_OWNER: {runtime_verify_owner}\nSTATE: verify_pending\nNEXT_CONTROL_SEQ: {next_control_seq}\nLATEST_WORK: {latest_work_path}\nLATEST_VERIFY: {latest_verify_path}\nRUNTIME_ENABLED_LANES: {runtime_enabled_lanes}\nREAD_FIRST:\n- {runtime_verify_read_first_doc}\n- work/README.md\n- verify/README.md\n- .pipeline/README.md\nSCOPE_HINT:\n{verify_scope_hint}\nOUTPUTS:\n- /verify verification note if needed\n- .pipeline/claude_handoff.md for STATUS: implement + CONTROL_SEQ: {next_control_seq}\n- .pipeline/gemini_request.md when Codex cannot narrow after tie-break + CONTROL_SEQ: {next_control_seq}\n- .pipeline/operator_request.md only when Gemini still cannot resolve it + CONTROL_SEQ: {next_control_seq}\nRULES:\n- role ownership is runtime metadata only; keep this verify contract lane-neutral\n- latest /work first, then same-day latest /verify if any\n- never route needs_operator to Claude\n- when writing a control slot, put CONTROL_SEQ immediately after STATUS and use exactly {next_control_seq}\n- keep one exact next slice or one exact operator decision only"
    IMPLEMENT_PROMPT="ROLE: implement\nROLE_OWNER: {runtime_implement_owner}\nSTATE: implement_ready\nHANDOFF: {active_handoff_path}\nHANDOFF_SHA: {active_handoff_sha}\nRUNTIME_ENABLED_LANES: {runtime_enabled_lanes}\nREAD_FIRST:\n- {runtime_implement_read_first_doc}\n- work/README.md\n- .pipeline/README.md\n- {active_handoff_path}\nRULES:\n- role ownership is runtime metadata only; keep this implement contract lane-neutral\n- implement only the bounded slice from the handoff\n- if the slice is completed, leave a `/work` closeout note; `.pipeline` does not replace `/work`\n- do not use `report/` as the primary implementation closeout for a normal implement round\n- do not ask the operator to choose among options\n- do not self-select the next slice\n- do not write or update .pipeline/gemini_request.md or .pipeline/operator_request.md\n- if the handoff is blocked or not actionable, emit the exact sentinel below and stop\nBLOCKED_SENTINEL:\nSTATUS: implement_blocked\nBLOCK_REASON: <short_reason>\nREQUEST: verify_triage\nHANDOFF: {active_handoff_path}\nHANDOFF_SHA: {active_handoff_sha}\nBLOCK_ID: {active_handoff_sha}:<short_reason>"
    ADVISORY_PROMPT="ROLE: advisory\nROLE_OWNER: {runtime_advisory_owner}\nSTATE: advisory_request_open\nNEXT_CONTROL_SEQ: {next_control_seq}\nRUNTIME_ENABLED_LANES: {runtime_enabled_lanes}\nOpen these files now:\n- @{runtime_advisory_read_first_doc}\n- .pipeline/README.md\n- {gemini_request_mention}\n- {latest_work_mention}\n- {latest_verify_mention}\nWrite exactly two files using edit/write tools only:\n- advisory log: {gemini_report_path}\n- recommendation slot: {gemini_advice_path} with STATUS: advice_ready and CONTROL_SEQ: {next_control_seq}\nKeep this advisory contract role-neutral even if the owner lane is not the default advisory lane.\nDo not use shell heredoc, shell redirection, cat > file, or printf > file.\nDo not modify any other repo files.\nWrite CONTROL_SEQ immediately after STATUS using exactly {next_control_seq}.\nKeep the recommendation short and exact."
    FOLLOWUP_PROMPT="ROLE: followup\nROLE_OWNER: {runtime_verify_owner}\nSTATE: advisory_advice_ready\nNEXT_CONTROL_SEQ: {next_control_seq}\nREQUEST: .pipeline/gemini_request.md\nADVICE: .pipeline/gemini_advice.md\nLATEST_WORK: {latest_work_path}\nLATEST_VERIFY: {latest_verify_path}\nRUNTIME_ENABLED_LANES: {runtime_enabled_lanes}\nREAD_FIRST:\n- {runtime_verify_read_first_doc}\n- verify/README.md\n- .pipeline/README.md\n- .pipeline/gemini_request.md\n- .pipeline/gemini_advice.md\nOUTPUTS:\n- .pipeline/claude_handoff.md for STATUS: implement + CONTROL_SEQ: {next_control_seq}\n- .pipeline/operator_request.md for STATUS: needs_operator + CONTROL_SEQ: {next_control_seq}\nRULES:\n- role ownership is runtime metadata only; keep this followup contract lane-neutral\n- when writing a control slot, put CONTROL_SEQ immediately after STATUS and use exactly {next_control_seq}"
    EXP_LOG_QUOTED=$(printf '%q' "$PROJECT_ROOT/.pipeline/logs/experimental/watcher.log")
    EXP_CMD=(
        python3 "$WATCHER_CORE_PY"
        --watch-dir "$PROJECT_ROOT/work"
        --base-dir "$PROJECT_ROOT/.pipeline"
        --repo-root "$PROJECT_ROOT"
        --verify-pane-target "$CODEX_PANE"
        --claude-pane-target "$CLAUDE_PANE"
        --gemini-pane-target "$GEMINI_PANE"
        --verify-prompt "$VERIFY_PROMPT"
        --implement-prompt "$IMPLEMENT_PROMPT"
        --advisory-prompt "$ADVISORY_PROMPT"
        --followup-prompt "$FOLLOWUP_PROMPT"
        --startup-grace 8
        --lease-ttl 600
    )
    EXP_CMD_STR=$(printf '%q ' "${EXP_CMD[@]}")
    EXP_WATCHER_PANE=$(tmux new-window -d -P -F '#{pane_id}' -t "$SESSION" -n watcher-exp -c "$PROJECT_ROOT" "exec ${EXP_CMD_STR}> $EXP_LOG_QUOTED 2>&1")
    tmux display-message -p -t "$EXP_WATCHER_PANE" '#{pane_pid}' > "$PROJECT_ROOT/.pipeline/experimental.pid"
    echo -e "${GRAY}  experimental watcher pane: $EXP_WATCHER_PANE  PID: $(cat "$PROJECT_ROOT/.pipeline/experimental.pid")${NC}"

    spawn_token_collector_tmux
else
    echo -e "${GRAY}[4/4] experimental 건너뜀${NC}"
fi

# ------------------------------------------------------------
# 완료 안내
# ------------------------------------------------------------
echo ""
echo -e "${CYAN}============================================${NC}"
echo -e "${GREEN}  파이프라인 실행 완료 [mode: $MODE]${NC}"
echo -e "${CYAN}============================================${NC}"
echo ""
echo -e "  tmux 접속:  ${YELLOW}tmux attach -t $SESSION${NC}"
echo -e "  A/B 집계:   ${YELLOW}python3 ab_compare.py .pipeline/logs${NC}"
echo -e "  전체 종료:  ${YELLOW}bash stop-pipeline.sh${NC}"
echo ""
if [ "$MODE" = "both" ]; then
    echo -e "${YELLOW}  ※ both 모드는 A/B 비교에 적합하지 않습니다.${NC}"
    echo ""
fi

if [ "$NO_ATTACH" -ne 1 ]; then
    tmux attach -t "$SESSION"
fi
