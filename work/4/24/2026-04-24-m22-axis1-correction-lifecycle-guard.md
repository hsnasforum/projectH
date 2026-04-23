# 2026-04-24 M22 Axis 1 correction lifecycle state-order guard

## 변경 파일
- `storage/sqlite_store.py`
- `tests/test_sqlite_store.py`
- `docs/MILESTONES.md`
- `work/4/24/2026-04-24-m22-axis1-correction-lifecycle-guard.md`

## 사용 skill
- `onboard-lite`: implement handoff, role harness, 관련 storage/test/doc 경계를 먼저 확인하고 범위를 세 파일로 고정했습니다.
- `finalize-lite`: handoff acceptance에 적힌 검증만 좁게 재실행하고 `/work` closeout 준비 여부를 사실 기준으로 정리했습니다.

## 변경 이유
- advisory seq 93과 implement handoff seq 94는 M22 Axis 1 목표를 `SQLiteCorrectionStore._transition()`의 상태 순서 가드로 정의했습니다.
- M21 Axis 1에서 SQLite correction lifecycle 메서드는 추가됐지만, 현재 `_transition()`은 현재 상태를 보지 않고 어떤 target status든 그대로 반영해서 잘못된 순서의 전이가 조용히 성공하는 리스크가 남아 있었습니다.
- 이번 라운드는 SQLite 기본 백엔드의 현재 리스크를 줄이는 bounded slice이며, JSON store나 브라우저 계약 확장은 범위 밖입니다.

## 핵심 변경
- `storage/sqlite_store.py`
  - `CORRECTION_STATUS_TRANSITIONS`를 import했습니다.
  - `SQLiteCorrectionStore._transition()`에서 현재 row의 `status`를 읽어 허용된 다음 상태인지 확인하고, 허용되지 않은 전이면 `None`을 바로 반환하도록 가드를 추가했습니다.
  - 기존 missing-id와 같은 `None` 반환 규칙을 유지했고, 네 개의 public lifecycle 메서드는 수정하지 않았습니다.
- `tests/test_sqlite_store.py`
  - 기존 lifecycle 성공 테스트를 실제 허용 순서에 맞게 정리했습니다.
    - `promote_correction`은 `confirm_correction` 이후
    - `activate_correction`은 `confirm_correction` + `promote_correction` 이후
    - `stop_correction`은 `confirm_correction` + `promote_correction` + `activate_correction` 이후
  - 신규 guard 테스트 3개를 추가했습니다.
    - `recorded -> active` 직접 전이는 `None` 반환, 상태 유지
    - `stopped -> confirmed` 재진입 전이는 `None` 반환, 상태 유지
    - `recorded -> confirmed -> promoted -> active -> stopped` 정상 체인은 모두 성공
- `docs/MILESTONES.md`
  - M21 종료 바로 아래에 `Milestone 22: Correction Lifecycle Integrity` 정의, guardrails, Axis 1 shipped entry를 추가했습니다.

## 검증
- `python3 -m py_compile storage/sqlite_store.py`
  - 통과: 출력 없음
- `python3 -m unittest tests.test_sqlite_store -v`
  - 통과: `Ran 29 tests in 0.081s`, `OK`
  - 신규 guard 테스트 3건 포함:
    - `test_transition_guard_rejects_out_of_order`
    - `test_transition_guard_rejects_from_stopped`
    - `test_transition_guard_allows_valid_chain`
- `git diff --check -- storage/sqlite_store.py tests/test_sqlite_store.py docs/MILESTONES.md`
  - 통과: 출력 없음

## 남은 리스크
- handoff 경계에 따라 `storage/correction_store.py` JSON backend는 이번 Axis 1에서 가드하지 않았습니다. 현재 기본 백엔드는 SQLite라서 우선순위는 낮지만, parity 관점에서는 후속 판단 여지가 남아 있습니다.
- 이번 라운드는 storage-layer/unit-test/doc sync만 다뤘으므로 browser/integration 검증은 재실행하지 않았습니다. 현 변경은 UI contract를 직접 바꾸지 않지만, verify lane에서 필요 시 더 넓은 회귀 확인이 필요할 수 있습니다.
- 작업 시작 시점에 이미 존재하던 unrelated dirty/untracked 상태(`pipeline_runtime/operator_autonomy.py`, `tests/test_operator_request_schema.py`, `tests/test_pipeline_runtime_supervisor.py`, `watcher_prompt_assembly.py`, 일부 `report/gemini/*`, `work/4/23/*`)는 건드리지 않았습니다.
