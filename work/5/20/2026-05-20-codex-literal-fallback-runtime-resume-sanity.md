# 2026-05-20 codex literal fallback runtime resume sanity

## 변경 파일

- `work/5/20/2026-05-20-codex-literal-fallback-runtime-resume-sanity.md`
- 이번 라운드에서는 `watcher_dispatch.py`와 `tests/test_watcher_core.py`를 수정하지 않았습니다.

## 사용 skill

- `work-log-closeout`: handoff #1992의 실제 실행 명령, runtime surface 관찰, publication-held 경계, 남은 리스크를 한국어 `/work` closeout으로 남기기 위해 사용했습니다.

## 변경 이유

- `.pipeline/implement_handoff.md#1992`가 Codex literal fallback dash-chunk repair 이후 작은 runtime resume sanity를 요구했습니다.
- 이전 repair는 `watcher_dispatch._send_literal_text_to_pane()`에 tmux option terminator `--`를 추가했고, dash-leading chunk 회귀 테스트를 추가했습니다.
- 이번 라운드는 새 source edit 없이 current runtime status, watcher log, focused dispatch checks를 다시 확인하는 closeout입니다.
- publication은 계속 held 상태이며 commit, push, branch/PR publication, PR creation/reuse/update, merge, release, external publication은 수행하지 않았습니다.

## 핵심 변경

- handoff SHA `4c690a0d3f32c67ea374ed56c64612a30f925d9fab0ae8143baa512684bb906a` 일치를 확인했습니다.
- `.pipeline/current_run.json`이 `.pipeline/runs/20260520T041821Z-p1140/status.json`과 `events.jsonl`을 가리키는 것을 확인했습니다.
- 최초 status 확인 시 `runtime_state=DEGRADED`, `degraded_reason=codex_verify_dispatch_failure_loop`였고 active round는 `work/5/20/2026-05-20-codex-literal-fallback-runtime-resume-sanity.md` verify dispatch였습니다.
- watcher log에서는 이전 pending verify job이 `matching_verify_already_exists`로 archive됐고, 새 `invalid flag -` 재시도 루프는 보이지 않았습니다. 대신 Codex pane readiness/submit 쪽 실패가 `codex pane not ready for dispatch` 및 `dispatch_failed_submit`으로 관찰됐습니다.
- focused dispatch compile/unit checks는 통과했습니다.
- 최종 status 재확인 시 `degraded_reason`은 cleared됐지만 `automation_health=needs_operator`, `automation_reason_code=codex_verify_lane_prompt_contamination`, active control `.pipeline/operator_request.md#1993` 상태였습니다. 이 operator request는 이번 implement lane에서 작성하지 않았습니다.

## 검증

- `sha256sum .pipeline/implement_handoff.md`
  - 결과: PASS. 요청 SHA `4c690a0d3f32c67ea374ed56c64612a30f925d9fab0ae8143baa512684bb906a`와 일치했습니다.
- `sed -n '1,220p' .pipeline/current_run.json`
  - 결과: PASS. current run은 `20260520T041821Z-p1140`, status path는 `.pipeline/runs/20260520T041821Z-p1140/status.json`로 확인했습니다.
- `sed -n '1,260p' .pipeline/runs/20260520T041821Z-p1140/status.json`
  - 결과: CHECK. 최초 확인 시 `runtime_state=DEGRADED`, `degraded_reason=codex_verify_dispatch_failure_loop`, `automation_next_action=operator_required`였습니다.
- `tail -160 .pipeline/logs/experimental/watcher.log`
  - 결과: CHECK. 이전 stale job archive `matching_verify_already_exists`를 확인했습니다. 최신 실패는 `invalid flag -`가 아니라 `codex pane not ready for dispatch (timeout=10.0s)` 반복 이후 `dispatch_failure_loop_degraded`였습니다.
- `tail -120 .pipeline/runs/20260520T041821Z-p1140/events.jsonl`
  - 결과: CHECK. `dispatch_stall_detected` / `automation_incident`가 `dispatch_failed_submit` 및 `codex_verify_dispatch_failure_loop`로 기록된 것을 확인했습니다.
- `python3 -m py_compile watcher_dispatch.py tests/test_watcher_core.py`
  - 결과: PASS, 출력 없음.
- `python3 -m unittest -v tests.test_watcher_core.CodexDispatchConfirmationTest tests.test_watcher_core.VerifyPendingBackoffTest`
  - 결과: PASS. `Ran 32 tests in 6.529s`, `OK`.
- `git diff --check -- watcher_dispatch.py tests/test_watcher_core.py work/5/20/2026-05-20-codex-literal-fallback-runtime-resume-sanity.md`
  - 결과: PASS, 출력 없음.
- `rg -n "invalid flag -|codex_verify_dispatch_failure_loop|codex pane not ready|matching_verify_already_exists|dispatch_failed_submit|TASK_DONE|TASK_ACCEPTED" .pipeline/logs/experimental/watcher.log .pipeline/runs/20260520T041821Z-p1140/events.jsonl | tail -80`
  - 결과: CHECK. `matching_verify_already_exists`, `codex pane not ready`, `dispatch_failed_submit`, `codex_verify_dispatch_failure_loop`, 그리고 이후 `degraded_cleared`를 확인했습니다. `invalid flag -`는 최신 tail 결과에 없었습니다.
- `sed -n '1,180p' .pipeline/runs/20260520T041821Z-p1140/status.json`
  - 결과: CHECK. 최종 확인 시 `runtime_state=RUNNING`, `degraded_reason=""`였지만 `automation_health=needs_operator`, `automation_reason_code=codex_verify_lane_prompt_contamination`, active control `.pipeline/operator_request.md#1993`로 확인했습니다.

## 남은 리스크

- 이번 라운드는 runtime resume sanity와 focused dispatch unit guard입니다. `make controller-test`, Playwright, `make e2e-test`, controller startup, local socket probe, end-to-end live dispatch replay, long soak는 실행하지 않았습니다.
- dash-leading chunk의 `invalid flag -` 직접 재현은 최신 log tail에서 보이지 않았지만, Codex verify lane prompt contamination이 남아 automation이 operator gate로 전환됐습니다. 이는 handoff #1992의 source fix 범위 밖이며 이번 implement lane에서는 operator_request를 작성하거나 수정하지 않았습니다.
- `.pipeline/advisory_request.md`, `.pipeline/operator_request.md`, `/verify`, 다음 handoff는 작성하지 않았습니다.
- publication remains held. commit, push, branch/PR publication, PR creation/reuse/update, merge, release, external publication은 수행하지 않았습니다.
