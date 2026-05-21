STATUS: resolved_after_operator_intervention
WORK: work/5/20/2026-05-20-codex-literal-fallback-runtime-resume-sanity.md
PREVIOUS_VERIFY: verify/5/20/2026-05-20-codex-literal-fallback-dash-chunk-guard.md
CONTROL_SEQ_NEXT: 1993
ADVISORY_ENABLED: false

# 검증 기록

## 요약

`work/5/20/2026-05-20-codex-literal-fallback-runtime-resume-sanity.md`의
source/test 변경 없음 주장은 맞습니다. 이전 repair 자체의 compile/unit/whitespace
검증도 유지됩니다.

다만 live runtime resume은 최종 통과로 볼 수 없습니다. resume sanity closeout
뒤 watcher가 새 verify job
`20260520-2026-05-20-codex-literal-fallbac-30bacd6d`를 만들었지만 Codex pane이
prompt-ready로 돌아오지 않아 `codex pane not ready for dispatch`가 반복됐고,
다시 `codex_verify_dispatch_failure_loop` degraded 상태가 됐습니다. 이번 실패
로그에는 새 `invalid flag -`는 보이지 않았고, pane tail에는 이전 implement
prompt와 stray prompt text가 남아 있었습니다.

## 사용 skill

- `round-handoff`: 최신 `/work`와 runtime status/log를 대조했습니다.
- `security-gate`: tmux pane clear와 runtime dispatch 경계가 local-only
  범위인지 확인했습니다.
- `finalize-lite`: 검증 통과분과 미통과 runtime risk를 분리했습니다.

## 확인한 대상

- `work/5/20/2026-05-20-codex-literal-fallback-runtime-resume-sanity.md`
- `verify/5/20/2026-05-20-codex-literal-fallback-dash-chunk-guard.md`
- `.pipeline/runs/20260520T041821Z-p1140/status.json`
- `.pipeline/state/jobs/20260520-2026-05-20-codex-literal-fallbac-30bacd6d.json`
- `.pipeline/logs/experimental/watcher.log`
- Codex tmux pane tail via `tmux capture-pane -pt %1 -S -80`

## 실행한 검증

- `git diff --check -- watcher_dispatch.py tests/test_watcher_core.py verify/5/19/2026-05-19-publish-held-prompt-runtime-non-socket-aggregate-guard.md work/5/20/2026-05-20-codex-literal-fallback-dash-chunk-guard.md verify/5/20/2026-05-20-codex-literal-fallback-dash-chunk-guard.md work/5/20/2026-05-20-codex-literal-fallback-runtime-resume-sanity.md .pipeline/implement_handoff.md`
  - 결과: PASS, 출력 없음.
- `tmux capture-pane -pt %1 -S -80`
  - 결과: stale implement prompt와 stray prompt text가 보였습니다.
- `tmux send-keys -t %1 C-u && tmux send-keys -t %1 C-l`
  - 결과: 실행은 성공했지만, 이후 watcher verify retry가 다시 pane not ready
    상태로 실패했습니다.
- `sed -n '1,240p' .pipeline/runs/20260520T041821Z-p1140/status.json`
  - 결과: 현재 `runtime_state=DEGRADED`,
    `degraded_reason=codex_verify_dispatch_failure_loop`,
    `automation_health=needs_operator`,
    `automation_next_action=operator_required`.

## 실행하지 않은 검증

- controller startup, local socket probe, Playwright, `make e2e-test`,
  `make controller-test`, long soak는 실행하지 않았습니다.
- 이유: live verify lane 자체가 prompt-ready contamination으로 다시 degraded
  되었으므로 broader validation을 주장할 수 없습니다.

## 변경 파일

- `verify/5/20/2026-05-20-codex-literal-fallback-runtime-resume-sanity.md`
- `.pipeline/operator_request.md`

## 판정

- code repair는 유지됩니다. `watcher_dispatch.py`의 dash-leading chunk
  `invalid flag -` 직접 원인은 막았습니다.
- live verify lane은 아직 정상 resume으로 판정할 수 없습니다.
- 다음 control은 operator stop입니다. 자동으로 또 다른 implement slice를 쓰면
  stale prompt contamination을 재반복할 위험이 큽니다.

## 남은 리스크

- Codex pane에는 stale prompt/prompt-visible 흔적이 남아 있습니다.
- publication remains held. commit, push, branch/PR publication,
  PR creation/reuse/update, merge, release, external publication은 수행하지
  않았습니다.

## 후속 operator intervention 결과

- stale prompt clear 중 Codex pane이 `exit:0`으로 종료되어 local runtime
  restart가 필요해졌습니다.
- `python3 -m pipeline_runtime.cli restart . --no-attach`를 실행했습니다.
- 새 run은 `20260520T052912Z-p37036`입니다.
- Codex CLI update prompt는 업데이트를 실행하지 않고 `3. Skip until next
  version`으로 넘겼습니다.
- 재시작 후 `python3 -m pipeline_runtime.cli status . --json` 기준
  `runtime_state=RUNNING`, `automation_health=ok`,
  `automation_next_action=continue`, active control `none`, Codex lane `READY`
  상태를 확인했습니다.
- `.pipeline/operator_request.md#1993`과 `.pipeline/implement_handoff.md#1992`
  는 stale control slot으로 남지 않도록 `STATUS: superseded`로 중립화했습니다.
- stale `OPERATOR_WAIT` turn_state가 남아 한 번 더
  `python3 -m pipeline_runtime.cli restart . --no-attach`를 실행했습니다.
- 최종 status polling에서 `runtime_state=RUNNING`, `automation_health=ok`,
  active control `none`, `turn_state=IDLE`, Codex lane `READY`를 확인했습니다.

## 후속 prompt-visible sanity 확인

- 사용자 화면에서 Codex lane에 `Write tests for @filename` 줄이 보였고, 해당
  텍스트가 실제 입력 오염인지 확인했습니다.
- `tmux send-keys -t %18 C-u`, `C-g`, `Escape`, `C-l`, `End C-w...`는
  해당 줄을 비우지 못했습니다. `C-g`는 외부 편집기 단축키로 해석되어
  `Cannot open external editor` 안내만 남겼고, 프롬프트를 제출하지는
  않았습니다.
- active control이 없고 `turn_state=IDLE`인 상태였으므로
  `python3 -m pipeline_runtime.cli restart . --no-attach`로 local runtime만
  재시작했습니다.
- 최신 run은 `20260520T061527Z-p65317`이며,
  `runtime_state=RUNNING`, `automation_health=ok`,
  `automation_next_action=continue`, active control `none`,
  `turn_state=IDLE`, Codex lane `READY`, Codex pid `65494`, pane `%22`를
  확인했습니다.
- 재시작 뒤 pane에는 `Summarize recent commits` 예시 줄이 보입니다. 이전
  `Write tests for @filename`가 지속된 것이 아니라 Codex TUI의 idle prompt
  예시 표시로 판단했습니다.
