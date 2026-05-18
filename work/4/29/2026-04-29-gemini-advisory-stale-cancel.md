# 2026-04-29 Gemini advisory stale cancel guard

## 변경 파일
- `watcher_dispatch.py`
- `watcher_core.py`
- `tests/test_watcher_core.py`
- `.pipeline/README.md`
- `docs/projectH_pipeline_runtime_docs/03_기술설계_명세서.md`
- `docs/projectH_pipeline_runtime_docs/05_운영_RUNBOOK.md`
- `.pipeline/advisory_advice.md` (rolling control slot, local runtime artifact)
- `report/gemini/2026-04-29-m84-after-m83-doc-sync.md`
- `work/4/29/2026-04-29-gemini-advisory-stale-cancel.md`

## 사용 skill
- `security-gate`: tmux `Escape` 자동 입력, runtime event/log payload, shell-control boundary를 좁게 점검.
- `doc-sync`: watcher 동작 변경을 runtime README / 기술설계 / 운영 RUNBOOK에 맞춰 반영.
- `finalize-lite`: 실행한 검증과 남은 리스크만 기준으로 wrap-up 범위 확인.
- `work-log-closeout`: 구현 라운드 closeout note 작성.

## 변경 이유
- Gemini advisory pane이 현재 active control과 무관한 오래된 `ROLE: advisory` 프롬프트에서 2시간 이상 `Thinking...` 상태로 남아 있었다.
- 즉시 복구로 `.pipeline/advisory_advice.md`를 `CONTROL_SEQ: 1302`, `RECOMMEND: A`로 작성해 verify/handoff follow-up으로 넘겼고, Gemini pane은 수동 `Escape`로 취소했다.
- 같은 상황이 재발해도 watcher가 stale advisory 작업을 좁게 취소하도록 runtime guard가 필요했다.

## 핵심 변경
- `watcher_dispatch.tmux_send_escape(...)`를 추가해 tmux pane `Escape` 입력도 기존 dispatch lock을 거쳐 처리하게 했다.
- `watcher_core.py`에 inactive advisory busy 추적을 추가했다. 현재 turn이 더 이상 active advisory가 아니거나 current advice가 이미 존재하는데 Gemini/advisory pane이 `ROLE: advisory` 프롬프트에서 busy이면 `inactive_advisory_cancel_sec` 이후 `Escape`를 보낸다.
- `advisory_recovery`로 verify/handoff에게 회수할 때도 stale advisory pane이 아직 busy이면 함께 취소한다.
- 취소 시 `advisory_lane_cancelled` runtime event를 남기며, reason / pane target / active control / visible `NEXT_CONTROL_SEQ` / snapshot hash를 기록한다.
- active `ADVISORY_ACTIVE + request_open` 자체는 inactive guard가 취소하지 않고 기존 `advisory_recovery` 경로가 맡도록 제한했다.
- 관련 runtime 문서에 read-only git permission auto-allow와 stale advisory cancel guard 운영 기준을 반영했다.

## 검증
- `python3 -m py_compile watcher_core.py watcher_dispatch.py pipeline_runtime/lane_surface.py` 통과.
- `python3 -m unittest -v tests.test_watcher_core.BusyLaneNotificationDeferTest.test_stale_advisory_recovers_to_verify_followup tests.test_watcher_core.BusyLaneNotificationDeferTest.test_stale_advisory_recovery_cancels_busy_advisory_lane tests.test_watcher_core.BusyLaneNotificationDeferTest.test_inactive_advisory_lane_cancel_sends_escape_after_grace tests.test_watcher_core.BusyLaneNotificationDeferTest.test_inactive_advisory_lane_cancel_skips_current_active_advisory` 통과.
- `python3 -m unittest -v tests.test_watcher_core.CodexDispatchConfirmationTest.test_answer_gemini_git_permission_prompt_selects_session_allow tests.test_watcher_core.CodexDispatchConfirmationTest.test_watcher_poll_answers_gemini_git_permission_prompt_before_startup_grace` 통과.
- `python3 -m unittest -v tests.test_watcher_core` 통과 (`Ran 215 tests ... OK`).
- `git diff --check -- watcher_core.py watcher_dispatch.py tests/test_watcher_core.py .pipeline/README.md docs/projectH_pipeline_runtime_docs/03_기술설계_명세서.md docs/projectH_pipeline_runtime_docs/05_운영_RUNBOOK.md` 통과.
- `python3 -m pipeline_runtime.cli status --json` 1차 확인: runtime `RUNNING`, automation health `ok`, Gemini `READY / prompt_visible`, watcher self-restart 후 pid 갱신 확인.
- closeout 이후 supervisor가 한 차례 `runtime_stopped`로 run을 닫았으나, local runtime을 재시작해 새 run `20260428T164723Z-p1895800` 기준 `RUNNING / ok / continue`로 복구했다. 최종 확인 시 Gemini는 `READY / prompt_visible`, Claude는 최신 work note 검증 중이었다.

## 남은 리스크
- Gemini 2시간 thinking은 해소됐고 runtime도 재시작되어 `RUNNING / ok` 상태다. 다만 최신 work note가 본 라운드 closeout으로 바뀌어 Claude verify가 이 note를 검증 중이다.
- 이번 라운드는 watcher runtime guard와 즉시 control unblock만 다뤘다. `/verify` note 작성, broad browser/E2E, PR/commit/push는 수행하지 않았다.
- 이전 라운드에서 이미 존재하던 다수의 untracked `work/`, `verify/`, `report/gemini/` 파일은 건드리지 않았다.
