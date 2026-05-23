# 2026-05-23 4축 소유권 번들 검증

STATUS: verified
BASED_ON_WORK: `work/5/23/2026-05-23-4-axis-owner-bundle.md`

## 검증 대상
- `pipeline_runtime/turn_arbitration.py`
- `pipeline_runtime/supervisor.py`
- `watcher_state.py`
- `verify_fsm.py`
- `app/handlers/corrections.py`
- `pipeline_runtime/operator_autonomy.py`
- `controller/js/package.json`
- `tests/test_turn_arbitration.py`
- `tests/test_pipeline_runtime_supervisor.py`
- `tests/test_verify_fsm.py`
- `tests/test_watcher_core.py`
- `.pipeline/README.md`
- `work/5/23/2026-05-23-4-axis-owner-bundle.md`
- `verify/5/23/2026-05-23-4-axis-owner-bundle.md`

## 확인한 사실
- active round snapshot, `dispatch_control_seq`, verify task hint, stale active round suppression이 `pipeline_runtime/turn_arbitration.py`의 공용 판정으로 모였습니다.
- supervisor는 active round 선택, job match, stale suppression, verify task hint 계산을 공용 helper에 위임합니다.
- `status.control=none` 상태에서도 active round에 `job_id`와 `dispatch_id`가 남아 있으면 verify lane task hint가 유효하게 유지되는 회귀 테스트가 추가되었습니다.
- STOPPED runtime surface에서는 `RECEIPT_PENDING` active round가 Codex active lane을 붙잡지 않도록 비워지며, runtime sidecar cleanup과 stop path에서 stale lane lease가 해제됩니다.
- verify FSM은 새 verify round dispatch 전에 다른 round의 기존 lease를 정리합니다.
- 전체 discovery 중 드러난 기존 회귀 3건은 이번 검증 범위 안에서 함께 정리했습니다.
  - Node ESM 테스트가 `controller/js/state.js` named export를 읽도록 `controller/js/package.json`을 추가했습니다.
  - correction pattern promotion은 seeded recurrence 기준으로 `is_highly_reliable`를 계산하고 저장하도록 보정했습니다.
  - `publication_authorization` decision class는 `release_gate` 호환 alias로 정규화했습니다.

## 실행한 검증
- PASS: `python3 -m py_compile pipeline_runtime/turn_arbitration.py pipeline_runtime/supervisor.py watcher_state.py verify_fsm.py app/handlers/corrections.py pipeline_runtime/operator_autonomy.py`
- PASS: 핵심 회귀 42 tests OK
  - `tests.test_turn_arbitration`
  - `tests.test_verify_fsm`
  - supervisor active hint, STOPPED cleanup, lease release 관련 신규 테스트
  - `PaneLease.release_if_mismatched` 신규 테스트
  - full-suite 중 발견된 controller queue, correction reliability, operator request schema 단일 회귀 테스트
- PASS: `python3 -m unittest discover -v tests`
  - 결과: 2284 tests OK, skipped=5
- PASS: `git diff --check -- pipeline_runtime/turn_arbitration.py pipeline_runtime/supervisor.py watcher_state.py verify_fsm.py app/handlers/corrections.py pipeline_runtime/operator_autonomy.py controller/js/package.json tests/test_turn_arbitration.py tests/test_pipeline_runtime_supervisor.py tests/test_watcher_core.py tests/test_verify_fsm.py .pipeline/README.md`

## 남은 리스크
- live tmux watcher/supervisor runtime smoke는 이번 검증에서 실행하지 않았습니다. 변경이 runtime surface와 lease cleanup에 닿아 있으므로 다음 실제 runtime 운영 중 STOPPED 전환, 새 verify round 전환, receipt pending 이후 lane surface를 관찰하면 좋습니다.
- 기존 untracked `.claude/settings.local.json`, `Zone.Identifier`, `report/gemini/*` 파일들은 이번 작업 범위 밖이라 변경하거나 staging하지 않았습니다.
- GitHub push는 요구사항에 따라 실행하지 않고 local commit까지만 진행합니다.
