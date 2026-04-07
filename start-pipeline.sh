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

require_agent_bin "Claude" "$CLAUDE_BIN" || exit 1
require_agent_bin "Codex" "$CODEX_BIN" || exit 1
require_agent_bin "Gemini" "$GEMINI_BIN" || exit 1

# Capture pane IDs for reliable targeting (pane index can shift)
CLAUDE_PANE=$(tmux display-message -t "$SESSION:0.0" -p '#{pane_id}')
CODEX_PANE=$(tmux split-window -P -F '#{pane_id}' -h -t "$CLAUDE_PANE" -c "$PROJECT_ROOT" "bash")
GEMINI_PANE=$(tmux split-window -P -F '#{pane_id}' -h -t "$CODEX_PANE" -c "$PROJECT_ROOT" "bash")
tmux select-layout -t "$SESSION:0" even-horizontal

launch_agent_in_pane "$CLAUDE_PANE" "Claude" "exec \"$CLAUDE_BIN\" --dangerously-skip-permissions"
launch_agent_in_pane "$CODEX_PANE" "Codex" "exec \"$CODEX_BIN\" --ask-for-approval never --disable apps"
launch_agent_in_pane "$GEMINI_PANE" "Gemini" "exec \"$GEMINI_BIN\" --approval-mode auto_edit"

echo -e "${GRAY}  Claude pane: $CLAUDE_PANE  Codex pane: $CODEX_PANE  Gemini pane: $GEMINI_PANE${NC}"

echo -e "${GRAY}  tmux: $SESSION (Claude=$CLAUDE_PANE / Codex=$CODEX_PANE / Gemini=$GEMINI_PANE)${NC}"

wait_for_cli_ready "$CLAUDE_PANE" "Claude"
wait_for_cli_ready "$CODEX_PANE" "Codex"
wait_for_cli_ready "$GEMINI_PANE" "Gemini"
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
    VERIFY_PROMPT="ROLE: codex_verify\nSTATE: verify_pending\nLATEST_WORK: {latest_work_path}\nLATEST_VERIFY: {latest_verify_path}\nREAD_FIRST:\n- AGENTS.md\n- work/README.md\n- verify/README.md\n- .pipeline/README.md\nOUTPUTS:\n- /verify verification note if needed\n- .pipeline/claude_handoff.md for STATUS: implement\n- .pipeline/gemini_request.md when Codex cannot narrow after tie-break\n- .pipeline/operator_request.md only when Gemini still cannot resolve it\nRULES:\n- latest /work first, then same-day latest /verify if any\n- never route needs_operator to Claude\n- keep one exact next slice or one exact operator decision only"
    CLAUDE_PROMPT="ROLE: claude_implement\nSTATE: implement\nHANDOFF: .pipeline/claude_handoff.md\nREAD_FIRST:\n- CLAUDE.md\n- .pipeline/claude_handoff.md"
    GEMINI_PROMPT="ROLE: gemini_arbitrate\nSTATE: codex_needs_tiebreak\nOpen these files now:\n- @GEMINI.md\n- {gemini_request_mention}\n- @AGENTS.md\n- {latest_work_mention}\n- {latest_verify_mention}\nWrite exactly two files using edit/write tools only:\n- advisory log: {gemini_report_path}\n- recommendation slot: {gemini_advice_path}\nDo not use shell heredoc, shell redirection, cat > file, or printf > file.\nDo not modify any other repo files.\nKeep the recommendation short and exact."
    CODEX_FOLLOWUP_PROMPT="ROLE: codex_followup\nSTATE: gemini_advice_ready\nREQUEST: .pipeline/gemini_request.md\nADVICE: .pipeline/gemini_advice.md\nLATEST_WORK: {latest_work_path}\nLATEST_VERIFY: {latest_verify_path}\nREAD_FIRST:\n- AGENTS.md\n- verify/README.md\n- .pipeline/README.md\n- .pipeline/gemini_request.md\n- .pipeline/gemini_advice.md"
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
        --claude-prompt "$CLAUDE_PROMPT"
        --gemini-prompt "$GEMINI_PROMPT"
        --codex-followup-prompt "$CODEX_FOLLOWUP_PROMPT"
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
