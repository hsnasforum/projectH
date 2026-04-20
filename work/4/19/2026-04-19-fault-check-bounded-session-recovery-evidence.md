# 2026-04-19 fault-check bounded session recovery evidence

## 변경 파일
- 이번 라운드 직접 편집:
  - `scripts/pipeline_runtime_gate.py`
  - `tests/test_pipeline_runtime_gate.py`
  - `work/4/19/2026-04-19-fault-check-bounded-session-recovery-evidence.md`
- 이번 라운드 범위 밖의 기존 dirty worktree:
  - `.pipeline/README.md` (직전 `session_missing` bounded recovery / tmux scaffold surfacing 라운드 누적)
  - `pipeline_runtime/tmux_adapter.py`, `pipeline_runtime/supervisor.py`, `tests/test_pipeline_runtime_supervisor.py` (직전 same-family 라운드 산출물)
  - watcher/manual-cleanup, controller cozy, runtime docs/tests 등 이 슬라이스와 무관한 기존 편집

## 사용 skill
- `superpowers:using-superpowers`: 세션 시작 시 필수 skill 확인 규칙을 따르기 위해 사용.
- `superpowers:test-driven-development`: 먼저 기존 `session loss degraded` 테스트 기대치와 supervisor 계약(`session_missing` + BROKEN lane → bounded recovery)을 확인한 뒤 신규 회귀 4건을 먼저 설계하고, 구현이 그 계약에 맞는지 검증하는 순서를 지키기 위해 사용.
- `work-log-closeout`: 이번 fault-check 구현 라운드의 `/work` 기록을 repo 규약 형식으로 남기기 위해 사용.

## 변경 이유
- 직전 라운드들이 supervisor `_recover_missing_session()` bounded contract(`session_missing` + any BROKEN lane일 때만 1회 scaffold 재생성 + `session_recovery_completed` / `session_recovery_failed` terminal event)와 `TmuxAdapter.create_scaffold()`의 required failure surfacing을 truthfully 닫았습니다.
- 그러나 live adoption gate인 `scripts/pipeline_runtime_gate.py`의 `session loss degraded` 체크는 여전히 `runtime_state`, representative `session_missing`, secondary `*_recovery_failed`만 구조화해 남겼을 뿐 bounded session recovery terminal event 증거 자체는 요구하지 않고 있었습니다.
- 결과적으로 supervisor가 scaffold 재생성 시도를 잃어버리는 회귀가 생겨도 degraded 스냅샷에 `session_missing`만 남아 있으면 `fault-check`가 녹색으로 넘어갈 수 있는 same-family current risk가 남아 있었습니다. 이번 라운드는 그 가장 작은 다음 위험을 gate contract 차원에서 좁혀 막습니다.

## 핵심 변경
- `scripts/pipeline_runtime_gate.py`의 `session loss degraded` 체크에 supervisor 계약을 mirror한 `recovery_expected` 판정을 추가했습니다. 판정 기준은 degraded 스냅샷의 representative `session_missing` + `lanes[].state == "BROKEN"` 존재 여부로, supervisor의 `session_recovery_needed` 조건과 같은 의미를 유지합니다.
- `recovery_expected`가 True이면 `_wait_until`로 `events.jsonl`에서 terminal `session_recovery_completed` 또는 `session_recovery_failed` 이벤트를 기다리고, 관측된 이벤트에서 `attempt`, `result`, `error`, raw `event` 전체를 구조화 `data.session_recovery`에 싣습니다.
- `recovery_expected`가 False인 경로도 같은 스키마 키(`recovery_expected=False`, `broken_lane_names=[]`, `event_observed=False`, 빈 문자열/빈 dict 기본값)를 그대로 유지해 자동화가 detail 문자열 scraping 없이 “recovery가 기대되지 않아 terminal event가 필요하지 않았다”는 사실을 읽을 수 있게 했습니다.
- `session_loss_ok` 판정에 `(not recovery_expected) or event_observed` 조건을 추가해, 복구가 기대되었는데 terminal event가 관측되지 않은 경우 representative reason이 맞더라도 체크가 실패하도록 좁혔습니다. representative `session_missing` primary는 계속 유지하며 lane 실패 뒤로 밀리지 않습니다.
- detail 문자열에도 새 `session_recovery=` 평탄화 필드(recovery_expected, event_observed, event_type, attempt, result, error)를 덧붙였습니다. 기존 `reason=`, `reasons=`, `secondary_recovery_failures=` prefix와 내용은 그대로 두어 이전 assertion들과 markdown report가 계속 동일하게 읽힙니다.
- `tests/test_pipeline_runtime_gate.py`에 `_run_session_loss_with_events` 공용 fixture를 추가하고 같은 파일에 4개의 focused 회귀를 넣었습니다.
  - `test_session_loss_check_requires_bounded_session_recovery_completed_evidence`: `session_missing` + 3 lane BROKEN + terminal `session_recovery_completed` 이벤트 → 체크 통과, `session_recovery.event_type == "session_recovery_completed"`, `attempt=1`, `result="recreated"`.
  - `test_session_loss_check_accepts_bounded_session_recovery_failed_evidence`: terminal `session_recovery_failed` 이벤트가 관측되면 recovery_expected=True여도 gate가 녹색이며, `error`에 `"tmux split Codex pane failed"` 같은 raw message가 그대로 실립니다.
  - `test_session_loss_check_fails_when_recovery_expected_but_no_event_observed`: `session_missing` + BROKEN lane은 있는데 `events.jsonl`에 terminal session-recovery event가 없으면 체크가 실패하고, 구조화 payload는 `recovery_expected=True`, `event_observed=False`를 그대로 보존합니다.
  - `test_session_loss_check_does_not_overclaim_recovery_when_no_broken_lane`: degraded 스냅샷이 `session_missing`만 있고 lane은 READY이면 supervisor 계약상 recovery가 triggered되지 않으므로 `recovery_expected=False`로 남기고 terminal event를 요구하지 않으며 체크는 여전히 통과합니다.
- 이 라운드는 `fault-check` gate의 **동작 변경**을 포함합니다. 단순 test/docs truth 조정이 아니라, gate가 요구하는 evidence surface 자체가 넓어졌습니다. 단 supervisor/adapter 구현 본체는 이번 범위 밖이라 그대로 두었고, 새 contract가 이미 shipped 구현과 모순되지 않는 범위 안에서만 좁혀졌습니다.
- `.pipeline/README.md`는 이번 라운드에서 새로 건드리지 않았습니다. 기존 `session loss degraded` 관련 paragraph가 이미 `bounded session_recovery_started/completed` 경계 문구를 포함하고 있어, 이번 gate 변경이 그 문구와 충돌하지 않습니다. 기존 dirty 상태는 직전 라운드들의 누적분입니다.

## 검증
- `python3 -m py_compile scripts/pipeline_runtime_gate.py tests/test_pipeline_runtime_gate.py`
  - 결과: 통과(출력 없음)
- `python3 -m unittest -v tests.test_pipeline_runtime_gate`
  - 결과: `Ran 34 tests`, `OK` (신규 4건 포함 전원 통과)
- `git diff --check -- scripts/pipeline_runtime_gate.py tests/test_pipeline_runtime_gate.py .pipeline/README.md`
  - 결과: 출력 없음
- broad browser suite(`make e2e-test`)와 live `python3 scripts/pipeline_runtime_gate.py fault-check ...` 실행은 생략했습니다. 이번 라운드는 gate의 unit-level 계약만 좁혔고 browser/tmux 조작은 범위 밖이며, live 조작은 현재 automation 세션에 영향을 줄 수 있기 때문입니다.

## 남은 리스크
- 이번 라운드는 gate의 **unit contract**만 좁혔습니다. 실제 host에서 `session_missing` 이후 supervisor가 `session_recovery_started/completed/failed`를 확실히 emit하는지, 그리고 gate가 live `events.jsonl`을 읽어 같은 증거를 확보하는지는 `scripts/pipeline_runtime_gate.py fault-check` live 실행으로 한 번 더 확인하는 편이 맞습니다.
- `recovery_expected` 판정은 degraded 스냅샷의 `lanes[].state == "BROKEN"` 유무로 결정됩니다. supervisor가 미래에 lane state 표기를 바꾸면(예: `OFF` 조기 전이로 BROKEN을 건너뛰는 경우) 판정이 무음으로 False가 될 수 있습니다. 이 경우 새 lane state에 맞춰 gate 판정도 함께 넓혀야 합니다.
- terminal event 대기는 `_wait_until` 기본 interval(0.5s)과 timeout 20s를 씁니다. 실제 host에서 recovery emit이 이 budget 안에 도달하는지는 live 실행으로 확인해야 하며, 그 결과 timeout이 현실적으로 너무 빡빡하면 gate가 false fail로 넘어갈 수 있습니다.
- `.pipeline/README.md`는 이번 라운드에서 건드리지 않았지만, 향후 README에 `fault-check` terminal-event 요구 문구를 따로 남기면 drift가 생기지 않도록 gate/테스트 쪽과 같은 라운드에서 조정해야 합니다.
