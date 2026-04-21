# 2026-04-21 implement handoff idle release

## 변경 파일
- `.pipeline/README.md`
- `pipeline_runtime/operator_autonomy.py`
- `watcher_core.py`
- `tests/test_operator_request_schema.py`
- `tests/test_watcher_core.py`
- `work/4/21/2026-04-21-implement-handoff-idle-release.md`

## 사용 skill
- `security-gate`: watcher/control dispatch 변경이 사용자 파일 쓰기, 외부 네트워크, 삭제/덮어쓰기 동작을 새로 만들지 않고 runtime control/log 경계에만 머무르는지 점검했습니다.
- `doc-sync`: active implement 중 handoff hot-swap 금지 규칙에 새 idle-pane release 예외가 생긴 점을 `.pipeline/README.md`에 좁게 반영했습니다.
- `work-log-closeout`: 실행한 검증과 남은 리스크를 표준 `/work` closeout 형식으로 정리했습니다.

## 변경 이유
- active control은 `.pipeline/claude_handoff.md` `CONTROL_SEQ: 619`로 갱신됐지만 watcher turn state가 이전 implement seq에 남아, implement lane이 READY/idle이어도 새 handoff가 다시 전달되지 않는 정지 패턴이 발생했습니다.
- 같은 계열의 재발을 줄이기 위해 busy implement pane은 계속 보호하되, 더 높은 `CONTROL_SEQ` handoff가 active이고 이전 implement pane이 prompt-ready idle이면 stale turn state를 풀 수 있는 소유 경계 안의 회복 경로가 필요했습니다.
- seq 619 handoff가 지적한 metadata alias도 reason-code alias를 operator-policy / decision-class 정규화에 재사용하면서 깨질 수 있어, field별 정규화 책임을 분리했습니다.

## 핵심 변경
- `normalize_reason_code`, `normalize_operator_policy`, `normalize_decision_class`가 공용 lexical token 정규화만 공유하고, field별 semantic alias는 각 함수 안에서만 적용하도록 분리했습니다.
- `normalize_operator_policy("branch_complete_pending_milestone_transition")`가 `gate_24h`로 수렴하도록 보강했고, 기존 `stop_until_operator_decision -> immediate_publish` 경로는 유지했습니다.
- watcher가 active `IMPLEMENT_ACTIVE` 중 새 implement handoff를 보더라도, `handoff_seq > current_turn_seq`, dispatchable 상태, implement pane prompt-ready idle이 모두 참이면 `claude_handoff_idle_release`로 새 handoff를 재전달하도록 했습니다.
- busy implement pane에서는 기존처럼 hot-swap을 보류하고, `claude_handoff_deferred` raw event에 `dispatchable`, `release_ready`, `release_reason`, `current_turn_control_seq`를 남겨 다음 진단이 쉬워지게 했습니다.
- `tests/test_watcher_core.py`에 busy 중 보류와 idle 중 release 회귀 테스트를 추가했습니다.
- `.pipeline/README.md`에 busy pane 보호가 기본이며, stale seq 회복용 idle-pane 예외만 허용된다는 현재 동작을 반영했습니다.

## 검증
- `python3 -m py_compile pipeline_runtime/operator_autonomy.py watcher_core.py`
  - 통과
- `python3 -m unittest tests.test_operator_request_schema`
  - `Ran 8 tests in 0.001s`
  - `OK (skipped=1)`
- `python3 -m unittest tests.test_watcher_core.ClaudeHandoffHotSwapTest`
  - 실패: 잘못된 테스트 클래스명 선택자였습니다. 코드 실패가 아니라 `ClaudeHandoffDispatchTest` / `RollingSignalTransitionTest`가 실제 클래스입니다.
- `python3 -m unittest tests.test_watcher_core.ClaudeHandoffDispatchTest`
  - `Ran 5 tests in 0.109s`
  - `OK`
- `python3 -m unittest tests.test_watcher_core.RollingSignalTransitionTest`
  - `Ran 9 tests in 0.280s`
  - `OK`
- `python3 -m unittest tests.test_pipeline_runtime_supervisor.RuntimeSupervisorTest.test_classify_operator_candidate_seq617_raw_metadata_is_canonical`
  - `Ran 1 test in 0.000s`
  - `OK`
- `python3 -m unittest tests.test_watcher_core`
  - `Ran 152 tests in 7.923s`
  - `OK`
- `python3 -m unittest tests.test_pipeline_runtime_supervisor`
  - `Ran 107 tests in 1.087s`
  - `OK`
- `python3 -m unittest tests.test_pipeline_runtime_control_writers`
  - `Ran 7 tests in 0.010s`
  - `OK`
- `python3 -c "from pipeline_runtime.operator_autonomy import normalize_operator_policy; print(normalize_operator_policy('branch_complete_pending_milestone_transition'), normalize_operator_policy('branch_complete_pending_milestone_transition') == 'gate_24h')"`
  - `gate_24h True`
- `git diff --check -- .pipeline/README.md pipeline_runtime/operator_autonomy.py watcher_core.py tests/test_operator_request_schema.py tests/test_watcher_core.py`
  - 출력 없음, `rc=0`
- `python3 -m pipeline_runtime.cli restart /home/xpdlqj/code/projectH --no-attach`
  - 출력 없음, `rc=0`
- startup grace 이후 `.pipeline/state/turn_state.json` / run status 확인
  - `runtime_state = RUNNING`
  - `turn_state.state = VERIFY_ACTIVE`
  - `turn_state.reason = startup_turn_codex`
  - active verify lane: `Claude` `WORKING`
  - latest work: `4/21/2026-04-21-implement-handoff-idle-release.md`

## 남은 리스크
- 이번 라운드 말미에 runtime을 `restart --no-attach`로 재기동해 새 watcher가 `RUNNING` / `VERIFY_ACTIVE` 상태로 최신 `/work` 검증을 시작한 것까지 확인했습니다. 다만 background verify/handoff lane이 `/verify` note와 next control을 끝까지 닫는지는 이 closeout 작성 시점에는 아직 완료 확인하지 않았습니다.
- 이번 변경은 busy pane 보호를 유지하는 좁은 release 예외입니다. implement pane이 prompt-ready idle로 잘못 판정되는 경우를 막기 위해 기존 `_pane_text_is_idle` 판정에 의존합니다.
- 작업 시작 전부터 `.pipeline/README.md`, `watcher_core.py`, `tests/test_watcher_core.py`, `pipeline_runtime/control_writers.py`, `tests/test_pipeline_runtime_supervisor.py` 등에는 다른 라운드의 dirty change가 있었습니다. 이번 라운드는 그중 관련 파일 위에 필요한 변경만 더했고, unrelated dirty change는 되돌리지 않았습니다.
- 전체 `pytest`와 Playwright smoke는 이번 runtime handoff 회복 경로의 좁은 검증 범위를 넘어 실행하지 않았습니다.
