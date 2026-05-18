# 2026-04-29 Gemini active advisory stuck recovery

## 변경 파일
- `pipeline_runtime/lane_surface.py`
- `watcher_core.py`
- `watcher_prompt_assembly.py`
- `tests/test_watcher_core.py`
- `.pipeline/README.md`
- `docs/projectH_pipeline_runtime_docs/03_기술설계_명세서.md`
- `docs/projectH_pipeline_runtime_docs/05_운영_RUNBOOK.md`
- `.pipeline/advisory_request.md`
- `.pipeline/operator_request.md`
- `work/4/29/2026-04-29-gemini-active-advisory-recovery.md`

## 사용 skill
- `security-gate`: stale advisory 회복 중 tmux Escape를 보내는 런타임 제어 변경의 로컬/로그/복구 경계를 점검했습니다.
- `release-check`: handoff 전 변경 파일, 실행 검증, 문서 동기화 필요 여부, 남은 리스크를 확인했습니다.
- `doc-sync`: recovery prompt와 운영 문서가 같은 stale advisory 재개 금지 동작을 동일하게 설명하도록 맞췄습니다.
- `work-log-closeout`: 구현 라운드의 변경 파일, 실제 검증, 잔여 리스크를 `/work` 형식으로 기록했습니다.
- `finalize-lite`: 마무리 시점에 검증 사실, 문서 동기화, `/work` closeout 준비 상태를 한 번 더 점검했습니다.

## 변경 이유
- Gemini pane의 느낌표는 어제의 stale `approval_wait` 잔상과 달리 실제 `Thinking... (esc to cancel, 36m+)` 상태였습니다.
- 새 advisory request가 열릴 때 파일 mtime/turn timestamp가 갱신되어 기존 `advisory_recovery_sec` age 판정이 다시 리셋되는 동안, Gemini의 오래된 active thinking이 남아 자동 회복을 지연했습니다.
- 현재 stuck thinking은 `tmux send-keys -t %8 Escape`로 끊었고, watcher가 새 advisory 시도를 다시 dispatch하는 것을 확인했습니다.

## 핵심 변경
- `pipeline_runtime.lane_surface.pane_text_busy_age_seconds(...)`를 추가해 `esc to cancel, 36m 33s`와 `esc to interrupt, 18s` 같은 pane-visible busy 경과시간을 초 단위로 파싱합니다.
- `watcher_core._stale_advisory_recovery_marker()`가 request 파일 age뿐 아니라 advisory pane에 보이는 busy age도 함께 사용하도록 했습니다.
- busy age가 `advisory_recovery_sec`를 넘고 verify lane이 prompt-ready이면 stale advisory recovery로 전환합니다.
- recovery 시 advisory lane이 실제 busy이면 `tmux send-keys ... Escape`를 보내고 `advisory_lane_cancelled` runtime event를 남깁니다.
- recovery가 발생한 advisory request는 `STATUS: superseded`로 바꿔 같은 request가 Gemini에 재투입되지 않게 했습니다.
- 현재 turn이 advisory가 아닌데 Gemini가 busy이면 `inactive_advisory_lane_cancelled` event와 함께 Escape를 보내는 guard를 추가했습니다.
- watcher poll 순서를 조정해 inactive Gemini busy cancel guard가 `operator_retriage_no_next_control`의 새 advisory 승격보다 먼저 실행되게 했습니다.
- advisory recovery prompt에 같은 stale advisory request를 다시 열지 말고, 새 advisory가 필요할 때만 materially narrower evidence를 요구하도록 명시했습니다.
- `.pipeline/README.md`와 runtime 설계/운영 문서에 같은 재개 금지 규칙을 동기화했습니다.
- live loop 중이던 `.pipeline/advisory_request.md` CONTROL_SEQ 1428은 `gemini_advisory_loop_cancelled` 사유로 수동 supersede 처리했습니다.
- Claude recovery handoff가 같은 advisory request를 다시 열어 Gemini를 재투입하던 것을 확인했고, `.pipeline/operator_request.md` CONTROL_SEQ 1429를 `safety_stop`으로 세워 runtime을 `OPERATOR_WAIT`에 고정했습니다.
- 잔여 Claude/Gemini in-flight request는 Escape로 중단해 추가 control rewrite를 막았습니다.
- regression test로 fresh request여도 Gemini pane의 `36m 33s` busy age가 회복 조건을 만족하고 Escape가 호출되는 경로를 고정했습니다.

## 검증
- 통과: `python3 -m py_compile watcher_core.py pipeline_runtime/lane_surface.py tests/test_watcher_core.py`
- 통과: `python3 -m py_compile watcher_core.py watcher_prompt_assembly.py pipeline_runtime/lane_surface.py tests/test_watcher_core.py`
- 통과: `python3 -m unittest -v tests.test_watcher_core.BusyLaneNotificationDeferTest.test_stale_advisory_recovers_to_verify_followup tests.test_watcher_core.BusyLaneNotificationDeferTest.test_stale_advisory_recovery_uses_visible_advisory_busy_age tests.test_watcher_core.BusyLaneNotificationDeferTest.test_stale_advisory_recovery_skips_when_current_advice_exists`
- 통과: `python3 -m unittest -v tests.test_watcher_core.BusyLaneNotificationDeferTest.test_stale_advisory_recovery_uses_visible_advisory_busy_age`
- 통과: `python3 -m unittest -v tests.test_watcher_core.BusyLaneNotificationDeferTest.test_stale_advisory_recovery_uses_visible_advisory_busy_age tests.test_watcher_core.BusyLaneNotificationDeferTest.test_inactive_advisory_lane_busy_is_cancelled tests.test_watcher_core.BusyLaneNotificationDeferTest.test_active_advisory_lane_busy_is_not_inactive_cancelled`
- 통과: `python3 -m unittest -v tests.test_watcher_core.BusyLaneNotificationDeferTest.test_stale_advisory_recovers_to_verify_followup tests.test_watcher_core.BusyLaneNotificationDeferTest.test_stale_advisory_recovery_uses_visible_advisory_busy_age tests.test_watcher_core.BusyLaneNotificationDeferTest.test_stale_advisory_recovery_skips_when_current_advice_exists tests.test_watcher_core.BusyLaneNotificationDeferTest.test_inactive_advisory_lane_busy_is_cancelled tests.test_watcher_core.BusyLaneNotificationDeferTest.test_active_advisory_lane_busy_is_not_inactive_cancelled`
- 실패 후 정정: `python3 -m unittest -v ...BusyLaneNotificationDeferTest.test_operator_retriage_no_next_control_promotes_to_advisory_request ...test_inactive_advisory_busy_preempts_operator_retriage_promotion ...`는 두 테스트의 실제 class가 `RollingSignalTransitionTest`라 loader error로 실패했습니다.
- 통과: `python3 -m unittest -v tests.test_watcher_core.RollingSignalTransitionTest.test_operator_retriage_no_next_control_promotes_to_advisory_request tests.test_watcher_core.RollingSignalTransitionTest.test_inactive_advisory_busy_preempts_operator_retriage_promotion tests.test_watcher_core.RollingSignalTransitionTest.test_pr_merge_recovery_no_next_control_promotes_to_advisory_request tests.test_watcher_core.RollingSignalTransitionTest.test_operator_retriage_seq_only_bump_preserves_no_next_control_age`
- 통과: `python3 -m unittest tests.test_watcher_core` (`Ran 212 tests in 10.210s`, `OK`)
- 통과: `git diff --check -- watcher_core.py pipeline_runtime/lane_surface.py tests/test_watcher_core.py`
- 통과: `git diff --check -- watcher_core.py watcher_prompt_assembly.py tests/test_watcher_core.py .pipeline/README.md docs/projectH_pipeline_runtime_docs/03_기술설계_명세서.md docs/projectH_pipeline_runtime_docs/05_운영_RUNBOOK.md work/4/29/2026-04-29-gemini-active-advisory-recovery.md`
- 통과: 직접 파서 확인. `36m 33s -> 2193`, `18s -> 18`, `1h 2m 3s -> 3723`.
- 확인: `python3 -m pipeline_runtime.cli status . --json`에서 runtime은 `RUNNING`, turn은 `ADVISORY_ACTIVE`, watcher는 새 pid `482025`로 살아 있음을 확인했습니다.
- 확인: `python3 -m pipeline_runtime.cli restart .`로 새 watcher pid `510462`에 최신 코드를 로드했고, 이후 status에서 turn은 `VERIFY_FOLLOWUP`, active lane은 `Claude`, Gemini는 `READY` 상태임을 확인했습니다.
- 확인: `tmux send-keys -t %19 Escape`, `tmux send-keys -t %21 Escape` 후 `python3 -m pipeline_runtime.cli status . --json`에서 active control은 `.pipeline/operator_request.md` CONTROL_SEQ 1429, turn은 `OPERATOR_WAIT`, Claude/Codex/Gemini 모두 `READY`임을 확인했습니다.
- 확인: prompt/order guard와 문서 동기화 후 `python3 -m pipeline_runtime.cli restart .`를 다시 실행했고, status에서 run id `20260429T103523Z-p527543`, watcher pid `527864`, runtime `RUNNING`, turn `OPERATOR_WAIT`, Claude/Codex/Gemini 모두 `READY`임을 확인했습니다.

## 남은 리스크
- 현재 Gemini는 `Thinking` loop가 아니라 `READY`입니다. 자동화는 `safety_stop` operator boundary에서 멈춰 있으므로 Gemini advisory 재투입은 차단된 상태입니다.
- controller smoke와 장시간 soak는 이번 변경이 stale advisory recovery와 pane parser/prompt guard에 한정되어 실행하지 않았습니다.
- 변경은 로컬 tmux advisory lane Escape에 한정됩니다. 외부 publish, merge, 승인 레코드, 사용자 문서 저장 흐름은 건드리지 않았습니다.
