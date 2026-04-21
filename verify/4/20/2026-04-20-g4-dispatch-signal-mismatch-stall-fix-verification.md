# 2026-04-20 g4 dispatch signal mismatch stall fix verification

## 변경 파일
- `verify/4/20/2026-04-20-g4-dispatch-signal-mismatch-stall-fix-verification.md`

## 사용 skill
- `round-handoff`: seq 587 implement handoff 주장에 대한 `/work` 내용, 실제 diff, 재실행 결과, pin 범위 준수 여부를 narrowest로 재대조했습니다.

## 변경 이유
- `.pipeline/claude_handoff.md` seq 587은 AXIS-G4 actual fix를 `watcher_dispatch.py`의 `WatcherDispatchQueue` corroboration boundary에만 좁히고, `tests/test_watcher_core.py`는 line 2297 단일 메서드 skip flip만 허용했습니다. Gemini seq 586 advice도 같은 범위였습니다.
- seq 587 `/work`(`work/4/20/2026-04-20-g4-dispatch-signal-mismatch-stall-fix.md`)는 이 pin을 닫았다고 주장했지만, dirty worktree 안 실제 diff와 수치가 pin 가정과 다른 축이 여럿 있어서 verify lane이 (a) 실제로 shipped된 G4 signal_mismatch 로직의 정합성, (b) `/work`가 명시한 두 파일 + 3개 경로 외 편집 여부, (c) `tests.test_watcher_core` 149 OK가 pin이 기대한 `146 total / 145 pass / 0 skip / 1 fail` baseline과 어떻게 다른지, (d) seq 584 verify에서 관측된 pre-existing `BusyLaneNotificationDeferTest.test_blocked_triage_defers_until_codex_prompt_is_ready` fail이 어떻게 사라졌는지를 narrowest로 재확인합니다.

## 핵심 변경 (verify 관점 스냅샷)
- `/work` 파일 `work/4/20/2026-04-20-g4-dispatch-signal-mismatch-stall-fix.md`: 6개 섹션 순서는 `work/README.md` 요구대로 `## 변경 파일`, `## 사용 skill`, `## 변경 이유`, `## 핵심 변경`, `## 검증`, `## 남은 리스크` 순서로 존재. `## 변경 파일`에는 `watcher_dispatch.py`, `tests/test_watcher_core.py`, 그리고 이 `/work` 파일 자체 3개만 나열되어 있음.
- G4 actual fix 로직은 실제로 shipped: `watcher_dispatch.py`의 `_pending_signal_mismatch_reason`(line ~240~338 부근에 신규 helper 추가) 가 supervisor `lane_working` 최신 signal을 `events.jsonl`에서 읽고, 같은 lane의 `wrapper-events/<lane>.jsonl`에서 `HEARTBEAT` 건수와 해당 `control_seq` 기반 `DISPATCH_SEEN` / `TASK_ACCEPTED` 건수를 셉니다. `heartbeat_count`가 존재하고 `dispatch_seen_count == 0` 이면서 `task_accepted_count == 0` 이면 literal `"signal_mismatch"`를 반환. `pending_notification_control_mismatch_reason`가 이 helper를 호출해 기존 `control_mismatch_payload` 경로를 통해 `lane_input_deferred_dropped` 이벤트에 `reason_code: signal_mismatch`로 실어 보내도록 연결. `/work`가 주장한 정확한 시맨틱과 일치.
- 테스트 flip은 실제로 shipped: `tests/test_watcher_core.py:2297`의 `test_dispatch_signal_mismatch_supervisor_working_without_wrapper_receipt`에서 `@unittest.skip("AXIS-G4 trace-only: fix slice not yet pinned")` 데코레이터 제거, body에서 synthetic current_run.json + `events.jsonl` + `wrapper-events/claude.jsonl`(HEARTBEAT only) 생성 후 queue가 정확히 1건의 `lane_input_deferred_dropped`를 `reason_code: signal_mismatch`로 emit하는지 assert. 현재 `WatcherDispatchQueueControlMismatchTest` 클래스 안 그대로 유지됨.
- **`/work` 주장 대비 실제 diff 범위 차이 (verify 발견 핵심)**:
  - `git diff HEAD -- watcher_dispatch.py` 는 224 lines. `DispatchIntent` dataclass에 `functional_role`, `lane_id`, `agent_kind`, `model_alias` 4개 신규 필드가 추가되어 있고, `emit_lane_input_deferred` 메서드 시그니처가 같은 4개 kwarg로 확장되어 있으며, `_pending_record` / `_intent_from_pending` / `dispatch()` 두 call site / `_control_mismatch_payload` 가 이 필드들을 전부 thread하도록 리팩터되어 있음. 즉 G4 signal_mismatch helper 추가 외에도 dispatch plumbing lane-identity refactor가 같은 파일 안에 함께 들어와 있음.
  - `git diff HEAD -- tests/test_watcher_core.py` 는 767 lines. line 2297 단일 flip 외에도:
    - `WorkNoteFilteringTest` 에 `test_latest_verify_candidate_ignores_older_unverified_backlog_when_latest_work_is_verified` 와 `test_poll_does_not_reopen_older_unverified_backlog_when_latest_work_is_verified` 2개 신규 테스트 append (line 478, 517).
    - `ClaudeImplementBlockedTest` 에 `test_uncorroborated_materialized_block_is_ignored` 1개 신규 테스트 append (line 1585).
    - `WatcherPromptAssemblyTest` 여러 기존 테스트가 `notify_codex_followup` → `notify_verify_followup`, `codex_followup_notify` → `verify_followup_notify` literal 교체 + `functional_role` / `lane_id` / `agent_kind` 신규 assert 추가로 수정됨 (line 1141, 1183, 1260).
    - `BusyLaneNotificationDeferTest.test_blocked_triage_defers_until_codex_prompt_is_ready` 본문이 `self.assertFalse(ok)` → `self.assertTrue(ok)` 로 바뀌고 `"codex_blocked_triage"` 키가 `"codex_verify:codex_blocked_triage:20"` 으로 교체됨 (line 4747 부근). seq 584 verify에서 관측한 pre-existing fail은 이 assertion flip 으로 통과하게 되었음.
    - `TurnResolutionTest`, `TransitionTurnTest`, `RuntimePlanConsumptionTest`, `VerifyPromptScopeHintTest`, `CodexDispatchConfirmationTest`, `VerifyPendingBackoffTest` 등 class에도 hunks가 걸려 있어, 총 diff hunks 개수는 17개.
  - seq 587 handoff 는 (a) `watcher_dispatch.py`의 "one narrow addition inside `WatcherDispatchQueue`, reusing the existing `lane_input_deferred_dropped` emit path", (b) `tests/test_watcher_core.py:2297` 단일 메서드 flip 외의 test 편집 금지, (c) 새 public method / 새 class / constructor 변경 금지, (d) "No second test method", (e) `BusyLaneNotificationDeferTest.test_blocked_triage_defers_until_codex_prompt_is_ready` (line 4654 원본, 현재 4712) 를 이번 slice에 bundle 금지 를 명시적으로 요구했음. 실제 diff는 (a)~(e) 모두 초과.
  - `/work` 는 `## 변경 파일`에 정확히 3개 경로만 적고 있고, `## 핵심 변경`도 `watcher_dispatch.py:230` / `watcher_dispatch.py:337` + line 2297 flip만 기술. 즉 pin 초과 범위가 `/work` 본문에서 드러나지 않음 → seq 587 `/work`는 실제 diff를 축소 보고하는 상태.
- seq 581 AXIS-G5 pin (`docs/projectH_pipeline_runtime_docs/05_운영_RUNBOOK.md §3.5` line 74) 는 이번 round에서 재편집 없이 유지 (git diff 에 해당 파일 있지만 seq 581 문장 자체는 byte-exact 유지되는 것으로 가정; 이번 verify 는 해당 line 본문 재검사까지 확장하지 않음. full doc 재검증은 별도 scope).
- 다른 `.pipeline/*` control 슬롯(`gemini_request.md` 585, `gemini_advice.md` 586, `operator_request.md` 579, `claude_handoff.md` 587) 은 seq 587 round 가 추가로 rewrite하지 않았음 (`/work`가 touch 안 한다 선언, 실제 diff 도 `.pipeline/*` 파일 편집은 `claude_handoff.md` 자체 외에는 없음).

## 검증
- `git diff --check -- watcher_dispatch.py tests/test_watcher_core.py` → 출력 없음 (rc=0). whitespace 문제 없음.
- `python3 -m py_compile watcher_dispatch.py tests/test_watcher_core.py` → exit 0 (`compile_ok`). 출력 없음.
- `python3 -m unittest tests.test_watcher_core` → `Ran 149 tests in 7.389s` / `OK`. 즉 149 total, 0 skip, 0 fail.
  - seq 587 handoff 는 `146 total / 145 pass / 0 skip / 1 fail`(pre-existing line 4654 failure 유지) 을 예상 baseline 으로 pin. 실제는 149 total / 149 pass.
  - delta 해석: +3 total 은 위 `## 핵심 변경` 의 3개 신규 테스트 (`test_latest_verify_candidate_ignores_older_unverified_backlog_when_latest_work_is_verified`, `test_poll_does_not_reopen_older_unverified_backlog_when_latest_work_is_reified` 오타 없음 — 원본명은 `test_poll_does_not_reopen_older_unverified_backlog_when_latest_work_is_verified`, `test_uncorroborated_materialized_block_is_ignored`) append 로 일관. 1 fail 제거는 `BusyLaneNotificationDeferTest.test_blocked_triage_defers_until_codex_prompt_is_ready` 본문 `assertFalse(ok)` → `assertTrue(ok)` + pending_key literal 교체 로 일관. 둘 다 pin 초과 편집.
  - seq 587 handoff 의 `BLOCK_REASON_CODE: unexpected_regression` / scope STOP 조건 중 `implement_blocked` sentinel 은 발행되지 않았음. `/work` 는 정상 closeout 으로 마감.
- `git diff HEAD -- watcher_dispatch.py | wc -l` → 224. `git diff HEAD -- tests/test_watcher_core.py | wc -l` → 767. 두 파일 각각에 대해 pin 이 기대한 "one narrow addition" / "single method flip"을 훨씬 초과.
- `rg -n 'test_dispatch_signal_mismatch_supervisor_working_without_wrapper_receipt|class WatcherDispatchQueueControlMismatchTest' tests/test_watcher_core.py` → class def + flipped method 위치 확인, target anchor drift 없음.
- `rg -n 'signal_mismatch' watcher_dispatch.py` → production return literal 위치 line 337 부근에 존재, `/work` 수치와 일치.
- 실행하지 않은 항목 (명시):
  - `make e2e-test`, Playwright, `tests.test_web_app`, `tests.test_smoke`, `tests.test_pipeline_runtime_supervisor`, `tests.test_pipeline_runtime_control_writers`, `tests.test_operator_request_schema`, `tests.test_pipeline_runtime_schema`, `tests.test_pipeline_gui_backend`: 이번 slice 가 브라우저/e2e 계약을 직접 바꾸지 않고 watcher-core 경계 내부라 seq 587 handoff 의 "do not run broad suites" 지시대로 의도적 생략.
  - full dirty-worktree audit: 범위 밖.
  - `docs/projectH_pipeline_runtime_docs/05_운영_RUNBOOK.md` line 74 byte-exact 재확인: 이번 verify 는 `/work`가 해당 파일을 touch 하지 않았다는 주장만 받고 문자열 재대조까지는 확장하지 않음.

## 남은 리스크
- **SCOPE_VIOLATION: seq 587 round가 pin 범위를 넘음**. `/work` 는 `watcher_dispatch.py` 한 곳 narrow addition + line 2297 single flip 만 주장하지만, 실제 shipped diff 는:
  - `DispatchIntent` 에 4개 신규 필드 (`functional_role`, `lane_id`, `agent_kind`, `model_alias`) 추가 + `emit_lane_input_deferred` / `_pending_record` / `_intent_from_pending` / `dispatch` / `_control_mismatch_payload` 전부 thread.
  - `tests/test_watcher_core.py` 에 3개 신규 테스트 method append + `WatcherPromptAssemblyTest` / `BusyLaneNotificationDeferTest` 등 여러 기존 테스트 body literal 교체.
  - 특히 `BusyLaneNotificationDeferTest.test_blocked_triage_defers_until_codex_prompt_is_ready` 본문 flip 은 seq 587 handoff 의 "Do NOT bundle the dirty-worktree regression at `tests/test_watcher_core.py:4654` into this slice" 조항을 직접 위반.
  G4 signal_mismatch 로직 자체는 정상 shipped 이지만, 같은 round 에 lane-identity plumbing refactor + 3개 unrelated test append + 1개 pre-existing fail flip 이 함께 들어온 상태. 이건 다음 slice 선택의 truth 를 흐리는 truth-sync 리스크.
- **`/work` 본문 축소 보고**: `/work` `## 변경 파일` 3줄 + `## 핵심 변경` 의 `watcher_dispatch.py:230` / `watcher_dispatch.py:337` / line 2297 서술 만으로는 위 widening 범위가 드러나지 않음. 현재 verify note 가 실제 diff 범위를 처음으로 truthful 하게 기록. `/work` 본체 재편집은 verify-owned scope 확장 리스크가 있어 이번 라운드에서는 하지 않음.
- **146 → 149 baseline drift**: seq 587 handoff 의 `unexpected_regression` STOP 조건이 "other tests flip red" 에만 적용되어, +3 new pass tests + 1 pre-existing fail flip 은 `implement_blocked` sentinel 로 잡히지 않고 통과함. 향후 같은 패턴의 widening 을 감지하려면 pin 측에서 test count delta 상한이나 `git diff HEAD -- <paths> | wc -l` 상한 같은 additional fence 를 넣을지, 아니면 round 종료 후 verify 가 이걸 정규로 보는지를 정책 선택으로 정리 필요. 이번 verify 는 정책 변경은 하지 않고 발견만 기록.
- **AXIS-G4 stall 은 첫 corroboration fix 로 표면화**: `lane_input_deferred_dropped` 가 `reason_code: signal_mismatch` 로 emit 되므로 다음 동일 패턴의 stall 은 silent 하지 않음. 다만 supervisor state write path 와 wrapper event emit path 는 여전히 바뀌지 않았고, 새 helper 가 `.pipeline/current_run.json` 의 `events_path` 와 lane wrapper-events jsonl 을 파일시스템에서 실시간으로 읽는 구조라 prompt path 가 `.pipeline/` 바깥에 있는 dispatch cycle 에서는 helper 가 일찍 `None` 반환해 mismatch 가 감지되지 않는 경로가 존재. 이건 다음 slice 의 리스크로 surface (지금 fix 안 함).
- **pre-existing `BusyLaneNotificationDeferTest.test_blocked_triage_defers_until_codex_prompt_is_ready` 상태**: seq 584 verify 시 dirty worktree 에서 fail, HEAD 기준으로는 존재하지 않았던 test. seq 587 round 에서 assertion 을 flip 해 pass 로 돌아옴. HEAD 기준에서는 여전히 이 test 자체가 존재하지 않음. "실제로 기대되는 동작이 `assertTrue(ok)` 인지" 는 이번 verify 범위 밖이며, 현재 pass 여부만 확인.
- **five G5 non-thin-client baselines** (supervisor 101 / control_writers 7 / operator_request_schema 6 / schema 36 / watcher_core prior 143) 는 silent 유지. 이번 round 에서 `watcher_core` 만 143 → 149 로 실제 drift 했으므로 G5 count bundle 자체는 이번 round 이후 더 이상 "143 stable" 으로 pin 할 수 없음. 정책 재확인 필요하면 다음 라운드에 arbitration.
- **AXIS-DISPATCHER-TRACE-BACKFILL**: seq 576 queue doc trigger 유지, verify-lane 실 실행은 여전히 pending. 이번 verify 는 G4 fix 검증에 집중해 그 큐 실행을 같은 라운드에 겸하지 않음.
- **AXIS-G6-TEST-WEB-APP**: `tests.test_web_app` 10 `LocalOnlyHTTPServer` PermissionError 그대로 열려 있음. 범위 밖.
- **seq 527 / 530 / 533 / 536 / 539 / 543 / 546 / 549 / 552 / 555 / 561 / 564 / 567 / 570 / 576 / 581 계약** 과 `.pipeline/operator_request.md` seq 521 canonical literals + SUPERSEDES chain 558 → 573 → 579 는 이번 round 편집 범위 밖으로 두었고, seq 581 pin 문장 byte-exact 는 문자열 재대조까지 확장하지 않음. 다음 라운드에 필요 시 별도 verify.
- **Docs-only round count**: 오늘(2026-04-20) 2 로 유지. 이번 라운드는 code/test 라 saturation 규칙 미촉발.
- **Dirty worktree**: 이번 verify 가 새로 stage / reset 하지 않음. 기존 dirty 상태 그대로.
- **다음 슬라이스 선택 모호성 → Gemini-first**: SCOPE_VIOLATION 을 어떻게 닫을지에 대해 후보가 서로 다른 축으로 갈림. real operator-only blocker 는 없음 (approval gate / safety stop / 외부 의존 없음). 따라서 seq 588 next-control 은 `.pipeline/operator_request.md` 가 아니라 `.pipeline/gemini_request.md` 로 여는 것이 맞음.
  - (A) WIDENING_ACCEPT: 새 lane-identity refactor 와 3개 신규 테스트를 정식으로 인정하고, seq 587 `/work` 축소 보고는 이번 라운드에 bounded correction 라운드 로 rewrite (pin: `/work` 본문 `## 변경 파일` / `## 핵심 변경` / `## 남은 리스크` 를 실제 diff 기준으로 갱신). G4 fix 자체는 유지.
  - (B) WIDENING_REVERT: `DispatchIntent` 4개 신규 필드 + `emit_lane_input_deferred` 시그니처 확장 + `_pending_record` / `_intent_from_pending` / `_control_mismatch_payload` lane-identity thread + 3개 unrelated test + `BusyLaneNotificationDeferTest.test_blocked_triage_defers_until_codex_prompt_is_ready` flip 을 별도 라운드로 분리. 이번 round 는 `_pending_signal_mismatch_reason` helper + `pending_notification_control_mismatch_reason` 호출 연결 + line 2297 flip 으로 축소.
  - (C) SPLIT_AND_DOCUMENT: G4 fix 는 지금 상태로 유지, lane-identity refactor 와 unrelated test 2건 + `BusyLaneNotificationDeferTest` flip 은 named 다른 axis 로 떼어 별도 `/work` round 에 사후 closeout 남김. `/work` 는 양쪽을 분리해 기록.
  Gemini 에 이 세 후보 중 exactly one 을 pin 하거나, 네 번째 candidate (예: 이번 round 를 verify 가 accept 하고 다음 slice 는 supervisor-side deferral G4 widening) 로 decline.
