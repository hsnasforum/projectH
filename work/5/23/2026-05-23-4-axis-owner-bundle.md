# 2026-05-23 4축 소유권 번들

## 변경 파일
- `.pipeline/README.md`
- `app/handlers/corrections.py`
- `controller/js/package.json`
- `pipeline_runtime/operator_autonomy.py`
- `pipeline_runtime/supervisor.py`
- `pipeline_runtime/turn_arbitration.py`
- `watcher_state.py`
- `verify_fsm.py`
- `tests/test_pipeline_runtime_supervisor.py`
- `tests/test_turn_arbitration.py`
- `tests/test_verify_fsm.py`
- `tests/test_watcher_core.py`
- `work/5/23/2026-05-23-4-axis-owner-bundle.md`

## 사용 skill
- `onboard-lite`: 현재 runtime, watcher, supervisor, verify FSM 진입점과 기존 테스트 경계를 좁게 확인했습니다.
- `security-gate`: lock cleanup, control surface, operator metadata 정규화가 local-first/approval 경계를 넘지 않는지 확인했습니다.
- `doc-sync`: release-gate compatibility alias 문서를 `.pipeline/README.md`에 맞췄습니다.
- `release-check`, `finalize-lite`: 구현 후 문법, 핵심 회귀, 전체 discovery, diff 검증을 확인했습니다.
- `work-log-closeout`: 이번 구현 범위, 검증, 남은 리스크를 기록했습니다.

## 변경 이유
- watcher와 supervisor의 turn/control/active round 판정 기준이 같은 축을 보면서도 일부 helper 소유권이 갈라져 있어, stale active round와 verify hint surface가 런타임 상태에 따라 다르게 남을 수 있었습니다.
- `status.control=none`이어도 active verify round의 `job_id`와 `dispatch_id`가 살아 있으면 verify lane이 이어서 닫아야 하는데, task hint가 control slot 중심으로만 판단하면 현재 round를 놓칠 수 있었습니다.
- STOPPED 또는 새 round 전환 뒤 이전 lock, dispatch stall, autonomy 상태가 남으면 controller/launcher가 낡은 일을 현재 진행으로 오해할 수 있었습니다.

## 핵심 변경
- `pipeline_runtime/turn_arbitration.py`에 active round 선택, dispatch control seq, active round/job/artifact matching, stale active round suppression, verify task hint 판정을 모았습니다.
- `pipeline_runtime/supervisor.py`는 active round 선택, stale suppression, job match, verify task hint를 공용 helper로 위임하도록 정리했습니다.
- `active_round.dispatch_control_seq`를 public active round snapshot과 verify task hint에 보존해 `control=none` 상태에서도 `job_id + dispatch_id` 기반 verify hint가 활성화되도록 했습니다.
- STOPPED surface에서는 `RECEIPT_PENDING` active round도 public `active_round`에서 비우고 task hint를 초기화하도록 했습니다.
- runtime sidecar cleanup과 `_stop_runtime()`이 `.pipeline/locks`의 lane lease를 함께 해제하도록 했습니다.
- `PaneLease.release_if_mismatched()`를 추가하고 verify FSM이 새 verify round dispatch 전에 이전 round lease를 정리하도록 했습니다.
- full-suite에서 함께 드러난 계약 drift를 좁게 정리했습니다.
  - `controller/js/package.json`으로 Node ESM 테스트가 `controller/js/state.js` named export를 정확히 읽게 했습니다.
  - correction pattern promotion은 activation의 explicit reliability flag 대신 seeded recurrence 기준으로 `is_highly_reliable`를 계산하고 저장합니다.
  - `publication_authorization` decision class를 `release_gate` compatibility alias로 정규화했습니다.

## 검증
- PASS: `python3 -m py_compile pipeline_runtime/turn_arbitration.py pipeline_runtime/supervisor.py watcher_state.py verify_fsm.py app/handlers/corrections.py pipeline_runtime/operator_autonomy.py`
- PASS: 핵심 회귀 42 tests OK
  - `tests.test_turn_arbitration`
  - `tests.test_verify_fsm`
  - 신규 supervisor active hint / STOPPED cleanup / lease release 테스트
  - 신규 PaneLease mismatch 테스트
  - full-suite 중 발견된 controller queue, correction reliability, operator request schema 단일 회귀
- PASS: `python3 -m unittest discover -v tests`
  - 결과: 2284 tests OK, skipped=5
- PASS: `git diff --check -- pipeline_runtime/turn_arbitration.py pipeline_runtime/supervisor.py watcher_state.py verify_fsm.py app/handlers/corrections.py pipeline_runtime/operator_autonomy.py controller/js/package.json tests/test_turn_arbitration.py tests/test_pipeline_runtime_supervisor.py tests/test_watcher_core.py tests/test_verify_fsm.py .pipeline/README.md`

## 남은 리스크
- full discovery는 통과했지만 live tmux runtime smoke는 이번 라운드에서 실행하지 않았습니다. 변경이 runtime surface/lease cleanup 중심이라 다음 실제 watcher/supervisor 운영 중 STOPPED 전환과 새 verify round 전환을 관찰하면 좋습니다.
- 기존 untracked `Zone.Identifier`, `.claude/settings.local.json`, `report/gemini/*` 파일은 이번 번들 범위가 아니어서 건드리지 않았습니다.
- GitHub push는 요청대로 실행하지 않고 local commit까지만 진행합니다.
