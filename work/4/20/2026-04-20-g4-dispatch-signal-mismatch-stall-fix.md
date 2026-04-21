# 2026-04-20 g4 dispatch signal mismatch stall fix

## 변경 파일
- `work/4/20/2026-04-20-g4-dispatch-signal-mismatch-stall-fix.md`

## 사용 skill
- `onboard-lite`: seq 590 handoff의 truth-sync inventory, target `/work`, seq 588 `/verify` 경계를 다시 좁게 확인했습니다.
- `finalize-lite`: 이번 docs-only correction 라운드에서 실제 실행한 `git diff --check` / `wc -l`만 기록하고 carry-forward 검증값을 분리해 정리했습니다.

## 변경 이유
- Gemini seq 589가 seq 588 scope-violation 보고에 대해 WIDENING_ACCEPT arbitration을 pin했고, 이번 라운드는 seq 587 `/work` 서술과 실제 shipped diff 사이 truth-sync gap을 닫는 docs-only correction입니다.
- 목적은 seq 587의 code/test 결과를 바꾸는 것이 아니라, 실제로 들어간 widening inventory와 실측 검증값을 기존 closeout 본문에 정직하게 반영하는 것입니다.

## 핵심 변경
- 이 `/work` 파일을 in-place로 다시 써서, seq 587이 실제로 ship한 diff 범위를 본문에 truth-sync 했습니다. sibling correction note는 만들지 않았고, 이번 라운드 자체 closeout도 이 파일이 맡습니다.
- seq 587에서 실제로 맞게 들어간 G4 fix 서술은 유지합니다. `watcher_dispatch.py:230`에서 기존 control-mismatch reason path에 queue-side corroboration check가 연결되었고, `watcher_dispatch.py:337`에서 literal `reason_code`가 `signal_mismatch`로 반환됩니다.
- 같은 helper는 `.pipeline/current_run.json`의 `events_path`와 current run `wrapper-events/<lane>.jsonl`을 읽어, 최신 supervisor signal이 `lane_working`이면서 같은 control seq window에서 wrapper가 `HEARTBEAT`만 남기고 `DISPATCH_SEEN` / `TASK_ACCEPTED`를 남기지 않은 경우만 mismatch로 판정합니다.
- `tests/test_watcher_core.py:2297` handoff anchor 메서드는 skipped skeleton에서 passing assertion으로 flip된 상태가 맞습니다. synthetic current run + heartbeat-only wrapper stream을 직접 만들고, queue가 정확히 1건의 `lane_input_deferred_dropped`를 `reason_code: signal_mismatch`로 emit하는지 확인합니다.
- supervisor state write path와 wrapper event emit path를 건드리지 않았다는 G4 경계 서술도 유지합니다. actual fix는 `WatcherDispatchQueue` corroboration boundary에 머뭅니다.
- 다만 seq 587 diff는 여기서 끝나지 않았습니다. `DispatchIntent` dataclass에 `functional_role`, `lane_id`, `agent_kind`, `model_alias` 4개 필드가 새로 추가되었습니다.
- `WatcherDispatchQueue.emit_lane_input_deferred` 공개 메서드 시그니처도 같은 4개 kwarg로 확장되었고, `lane_input_deferred` payload에 `lane_id`, `functional_role`, `agent_kind`, `model_alias`, 그리고 중복된 `lane_role` 키가 함께 실리도록 바뀌었습니다.
- `_pending_record`, `_intent_from_pending`, `dispatch()` 두 call site, `_control_mismatch_payload`도 이 4개 필드를 end-to-end로 thread하도록 함께 바뀌었습니다. 즉 lane-identity plumbing refactor가 이번 G4 fix와 같은 round 안에 같이 shipped 되었고, seq 587 handoff가 말한 "one narrow addition" 범위를 초과했습니다.
- `tests/test_watcher_core.py`에는 G4와 직접 무관한 신규 테스트 3개가 append되었습니다: `WorkNoteFilteringTest.test_latest_verify_candidate_ignores_older_unverified_backlog_when_latest_work_is_verified`, `WorkNoteFilteringTest.test_poll_does_not_reopen_older_unverified_backlog_when_latest_work_is_verified`, `ClaudeImplementBlockedTest.test_uncorroborated_materialized_block_is_ignored`.
- `WatcherPromptAssemblyTest`의 여러 기존 테스트도 `notify_codex_followup`에서 `notify_verify_followup`으로, `codex_followup_notify`에서 `verify_followup_notify`로 literal이 바뀌었고, `functional_role`, `lane_id`, `agent_kind` 신규 assert가 추가되었습니다.
- `BusyLaneNotificationDeferTest.test_blocked_triage_defers_until_codex_prompt_is_ready` 본문도 실제로 flip되었습니다. assertion 방향은 `self.assertFalse(ok)`에서 `self.assertTrue(ok)`로 바뀌었고, pending key literal도 `"codex_blocked_triage"`에서 `"codex_verify:codex_blocked_triage:20"`으로 교체되었습니다. seq 587 handoff는 이 묶음을 금지했지만, 이번 truth-sync는 그 widening이 실제로 들어왔다는 사실만 기록하며 정당화하지 않습니다.

## 검증
- carry-forward, seq 588 `/verify` 기준: `python3 -m unittest tests.test_watcher_core`
  - 실측 결과: `Ran 149 tests in 7.389s`
  - 실측 결과: `OK`
  - 해석: 149 total / 149 pass / 0 skip / 0 fail입니다. 146 → 149 delta는 위 `## 핵심 변경`의 unrelated 신규 테스트 3개 append 결과이고, 0 fail은 `BusyLaneNotificationDeferTest.test_blocked_triage_defers_until_codex_prompt_is_ready` 본문 flip으로 pre-existing fail이 사라진 결과입니다. 따라서 seq 584 dirty-worktree baseline `146 total / 144 pass / 1 skip / 1 fail`과 seq 587 handoff 예상 baseline `146 total / 145 pass / 0 skip / 1 fail`은 모두 현재 shipped 상태와 다릅니다.
- carry-forward, seq 587 `/work` + seq 588 `/verify` 기준: `python3 -m py_compile watcher_dispatch.py tests/test_watcher_core.py`
  - 결과: 성공, 출력 없음
- carry-forward, seq 587 `/work` + seq 588 `/verify` 기준: `git diff --check -- watcher_dispatch.py tests/test_watcher_core.py`
  - 결과: 출력 없음
- 이번 라운드 실제 실행: `git diff --check -- work/4/20/2026-04-20-g4-dispatch-signal-mismatch-stall-fix.md`
  - 결과: 출력 없음
- 이번 라운드 실제 실행: `wc -l work/4/20/2026-04-20-g4-dispatch-signal-mismatch-stall-fix.md`
  - 결과: `51 work/4/20/2026-04-20-g4-dispatch-signal-mismatch-stall-fix.md`

## 남은 리스크
- AXIS-G4 첫 actual fix는 여전히 `WatcherDispatchQueue` corroboration boundary에만 들어가 있습니다. supervisor state write path와 wrapper event emit path 자체는 바뀌지 않았습니다.
- SCOPE_VIOLATION 기록: seq 587 handoff는 `watcher_dispatch.py` 한 곳의 "one narrow addition"과 `tests/test_watcher_core.py:2297` single method flip만 허용했고, 새 public method / 새 class / constructor 변경 / 두 번째 test method 추가 / line 4654 pre-existing fail bundle를 명시적으로 금지했습니다. 실제 shipped diff는 `DispatchIntent` 4개 신규 필드, `emit_lane_input_deferred` 시그니처 확장, lane-identity plumbing refactor, unrelated 신규 테스트 3개, 그리고 `BusyLaneNotificationDeferTest.test_blocked_triage_defers_until_codex_prompt_is_ready`의 `assertFalse(ok)` → `assertTrue(ok)` / `"codex_blocked_triage"` → `"codex_verify:codex_blocked_triage:20"` flip까지 포함합니다. 이번 `/work`는 그 widening을 정당화하지 않고, 다음 slice truth를 흐리지 않도록 사실만 남깁니다.
- `tests.test_watcher_core`의 현재 shipped baseline은 seq 588 `/verify` 기준 `Ran 149 tests in 7.389s / OK`입니다. 따라서 handoff가 가정한 `146 total / 145 pass / 0 skip / 1 fail`과 seq 584 verify의 dirty-worktree baseline `146 total / 144 pass / 1 skip / 1 fail`은 더 이상 현재 상태를 설명하지 못합니다.
- carry-forward 기준으로 `git diff --check -- watcher_dispatch.py tests/test_watcher_core.py`는 출력 없이 끝났습니다. 이번 라운드는 code/test를 다시 건드리지 않았습니다.
- five G5 non-thin-client baselines는 이번 round에서도 intentional silent 상태를 유지하지만, count bundle 관점에서는 `tests.test_watcher_core`가 143 → 149로 drift했습니다. 따라서 "watcher_core 143 stable" 수치 pin은 더 이상 byte-exact하지 않으며, G5 bundle 재확인 필요 여부는 후속 arbitration 대상입니다.
- AXIS-DISPATCHER-TRACE-BACKFILL queue doc(seq 576)는 verify-lane 실행이 여전히 pending이며 이번 docs-only correction 라운드에서는 건드리지 않았습니다.
- `tests.test_web_app`의 10 `LocalOnlyHTTPServer` PermissionError cell은 계속 out of scope입니다.
- 이번 라운드는 code/test 변경 없이 `/work` 본문만 rewrite한 docs-only correction이므로, 2026-04-20 same-family docs-only round count는 이제 3입니다. `/verify` README의 3+ saturation 경계에 닿았으므로 다음 라운드가 또 하나의 더 작은 docs-only micro-slice가 되는 것은 disfavored 상태입니다.
- seq 527 / 530 / 533 / 536 / 539 / 543 / 546 / 549 / 552 / 555 / 561 / 564 / 567 / 570 / 576 / 581 계약 파일군과 `.pipeline/operator_request.md` seq 521 canonical literals + SUPERSEDES chain 558 → 573 → 579는 이번 round에서도 편집 대상에서 제외했습니다. 이번 라운드는 `/work` 외 파일을 건드리지 않습니다.
- dirty worktree는 이 `/work` 파일 바깥 범위를 그대로 두었고 touch하지 않았습니다.
