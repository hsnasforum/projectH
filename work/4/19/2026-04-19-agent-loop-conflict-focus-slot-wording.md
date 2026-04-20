# 2026-04-19 agent-loop conflict focus-slot wording

## 변경 파일
- core/agent_loop.py
- tests/test_smoke.py

## 사용 skill
- release-check: handoff가 요구한 focused unittest, `py_compile`, `diff --check`만 다시 확인하고 문서/브라우저 재검증이 왜 불필요한지 범위 기준으로 정리했습니다.
- work-log-closeout: `/work` 표준 섹션 순서에 맞춰 이번 라운드의 실제 변경과 검증만 기록했습니다.

## 변경 이유
- `_build_claim_coverage_progress_summary`의 focus-slot unresolved branch는 CONFLICT 상태도 WEAK/MISSING과 같은 generic `"아직 {label} 상태"` 문장으로 처리하고 있어, handoff가 고정한 CONFLICT 전용 문구와 맞지 않았습니다.
- 이번 슬라이스 목표는 unresolved bucket이 raw status를 함께 들고 다니게 만든 뒤, focus-slot이 여전히 CONFLICT일 때만 `"출처들이 서로 어긋난 채 남아 있습니다."` 템플릿으로 분기시키는 것이었습니다.
- `_claim_coverage_status_rank`, `_claim_coverage_status_label`, `_build_entity_slot_probe_queries`, improved/regressed summary, browser/docs contract는 이번 라운드 범위에서 제외했습니다.

## 핵심 변경
- `core/agent_loop.py`에서 `unresolved_slots`를 `(slot, current_label, current_status)` tuple로 확장해 focus-slot unresolved branch가 현재 raw status를 직접 볼 수 있게 했습니다.
- 같은 함수의 focus-slot unresolved branch는 `cur_status == CoverageStatus.CONFLICT`일 때만 `재조사했지만 {slot}{focus_particle} 출처들이 서로 어긋난 채 남아 있습니다.`를 반환하고, WEAK/MISSING은 기존 `재조사했지만 {slot}{focus_particle} 아직 {current_label} 상태입니다.` 문구를 그대로 유지합니다.
- unresolved summary join은 tuple shape 변경에 맞춰 label만 읽도록 최소 수정했습니다. rank/label/probe guard와 improved/regressed branch는 건드리지 않았습니다.
- `tests/test_smoke.py`의 기존 `test_build_claim_coverage_progress_summary_focus_slot_conflict_stays_unresolved`는 새 CONFLICT 고정 문장을 exact match로 검증하도록 갱신했습니다.
- `tests/test_smoke.py`에 `test_build_claim_coverage_progress_summary_focus_slot_unresolved_wording_branches_by_status`를 추가해 CONFLICT, WEAK, MISSING의 exact wording을 각각 고정했습니다.
- `core/agent_loop.py`, `tests/test_smoke.py`에는 이번 라운드 이전 dirty hunk가 이미 있었고, 이번 작업은 handoff가 지정한 focus-slot wording 구간만 추가로 수정했습니다.

## 검증
- `python3 -m unittest tests.test_smoke -k coverage`
  - 1차 결과: `FAILED (failures=1)`; 기존 `test_build_claim_coverage_progress_summary_focus_slot_conflict_stays_unresolved`가 예전 `"정보 상충 상태"` 기대값을 유지하고 있어 실패했습니다.
  - 수정 후 2차 결과: `Ran 13 tests in 0.070s`, `OK`
- `python3 -m py_compile core/agent_loop.py tests/test_smoke.py`
  - 결과: 출력 없음, 통과
- `git diff --check -- core/agent_loop.py tests/test_smoke.py`
  - 결과: 출력 없음, 통과
- Playwright, `python3 -m unittest tests.test_web_app`, docs sync 재검증은 실행하지 않았습니다. 이번 라운드는 서버가 만드는 focus-slot progress 문장 한 갈래와 그에 대응하는 focused unittest만 바뀌었고, browser helper, persisted schema, renderer contract는 변경하지 않았습니다.

## 남은 리스크
- Milestone 4의 `source role labeling/weighting`, reinvestigation trigger threshold, STRONG/WEAK/MISSING/CONFLICT 추가 분리 정책은 별도 후보로 남아 있습니다.
- response-body에서 별도 `[정보 상충]` tag를 내보내는 경로는 이번 슬라이스에 포함되지 않았습니다.
- unrelated `python3 -m unittest tests.test_web_app` failure family는 이번 handoff 범위 밖입니다.
