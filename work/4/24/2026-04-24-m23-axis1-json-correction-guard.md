# 2026-04-24 M23 Axis 1 JSON CorrectionStore state-order guard

## 변경 파일
- `storage/correction_store.py`
- `tests/test_correction_store.py`
- `docs/MILESTONES.md`
- `work/4/24/2026-04-24-m23-axis1-json-correction-guard.md`

## 사용 skill
- `onboard-lite`: implement handoff, role harness, JSON correction store/test/doc 경계를 먼저 확인하고 범위를 세 파일로 고정했습니다.
- `finalize-lite`: handoff acceptance에 적힌 검증만 좁게 실행하고 `/work` closeout 준비 여부를 실제 결과 기준으로 정리했습니다.

## 변경 이유
- advisory recovery seq 97과 implement handoff seq 98은 M23 Axis 1 목표를 JSON `CorrectionStore._transition()`의 상태 순서 가드로 정의했습니다.
- SQLite 경로는 M22 Axis 1에서 이미 `CORRECTION_STATUS_TRANSITIONS`를 적용했지만, `storage/correction_store.py`는 여전히 현재 상태를 보지 않고 어떤 target status든 그대로 반영해서 JSON backend parity gap이 남아 있었습니다.
- 이번 라운드는 기본 backend가 아닌 JSON 경로의 남아 있던 correction lifecycle 리스크를 줄이는 bounded parity slice이며, SQLite 경로나 브라우저 계약 확장은 범위 밖입니다.

## 핵심 변경
- `storage/correction_store.py`
  - `CORRECTION_STATUS_TRANSITIONS`를 import했습니다.
  - `CorrectionStore._transition()`에서 현재 record의 `status`를 읽어 허용된 다음 상태인지 확인하고, 허용되지 않은 전이면 `None`을 바로 반환하도록 가드를 추가했습니다.
  - 기존 missing-id와 같은 `None` 반환 규칙을 유지했고, 네 개의 public lifecycle 메서드는 수정하지 않았습니다.
- `tests/test_correction_store.py`
  - 기존 `test_lifecycle_transitions`는 valid chain을 이미 검증하고 있어 유지했습니다.
  - 신규 invalid-transition 테스트 2개를 추가했습니다.
    - `recorded -> active` 직접 전이는 `None` 반환, 상태 유지
    - `stopped -> confirmed` 재진입 전이는 `None` 반환, 상태 유지
- `docs/MILESTONES.md`
  - M22 종료 바로 아래에 `Milestone 23: Correction Lifecycle Integrity — JSON Parity` 정의, guardrails, Axis 1 shipped entry를 추가했습니다.

## 검증
- `python3 -m py_compile storage/correction_store.py`
  - 통과: 출력 없음
- `python3 -m unittest tests.test_correction_store -v`
  - 통과: `Ran 20 tests in 0.035s`, `OK`
  - 신규 guard 테스트 2건 포함:
    - `test_transition_guard_rejects_out_of_order`
    - `test_transition_guard_rejects_from_stopped`
- `git diff --check -- storage/correction_store.py tests/test_correction_store.py docs/MILESTONES.md`
  - 통과: 출력 없음

## 남은 리스크
- handoff 경계에 따라 `storage/sqlite_store.py`는 이번 라운드에서 건드리지 않았습니다. SQLite 경로는 M22 Axis 1에서 이미 가드되어 있으며, 이번 라운드는 JSON parity만 다뤘습니다.
- 이번 라운드는 storage-layer/unit-test/doc sync만 다뤘으므로 browser/integration 검증은 재실행하지 않았습니다. 현 변경은 UI contract를 직접 바꾸지 않지만, verify lane에서 필요 시 더 넓은 회귀 확인이 필요할 수 있습니다.
- 작업 시작 시점에 이미 존재하던 unrelated dirty/untracked 상태(`pipeline_runtime/operator_autonomy.py`, `tests/test_operator_request_schema.py`, `tests/test_pipeline_runtime_supervisor.py`, `watcher_prompt_assembly.py`, 일부 `report/gemini/*`, `work/4/23/*`)는 건드리지 않았습니다.
