# verify: 2026-05-21 state_contract refactor + events rotation (B9/D2)

## 대상 work
`work/5/21/2026-05-21-state-contract-refactor-events-rotation.md`

## 검증 결과: READY

## 재실행 검증

| 검사 | 결과 |
|---|---|
| `py_compile` state_contract / supervisor | PASS |
| `unittest` supervisor + state_contract 230개 | PASS (1.517s) |
| `git diff --check` | PASS |

## 코드 확인

| 항목 | 위치 | 확인 |
|---|---|---|
| B9: 섹션 헬퍼 5개 추출 (`_extract_autonomy/control/round/lane/queue`) | state_contract.py:334–430 | ✓ |
| B9: `reduce_runtime_snapshot()` 11줄 thin wrapper | state_contract.py:490 | ✓ |
| D2: `DEFAULT_EVENTS_MAX_LINES = 2000` 상수 | supervisor.py:126 | ✓ |
| D2: `_rotate_events_jsonl()` 메서드, 500 이벤트마다 트리거 | supervisor.py:446–461 | ✓ |
| D2: tail 1999줄 + marker 1줄 = 2000줄 보장 | supervisor.py:456 | ✓ |
| D2: 읽기/쓰기 실패 시 silent skip | supervisor.py: | ✓ |

## 설계 주목 사항

로테이션 후 `events_rotated` marker를 2000줄 안에 포함시키는 방식(1999+1)이
marker 누락 없이 파일 크기를 정확히 제어합니다. 올바른 설계입니다.
