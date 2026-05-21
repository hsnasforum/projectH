# verify: 2026-05-21 pipeline launcher Task 4-A/B structural stability

## 대상 work
`work/5/21/2026-05-21-pipeline-launcher-task4ab-structural-stability.md`

## 검증 결과: READY (Task 4-A/B 범위)

## 재실행 검증

| 검사 | 결과 |
|---|---|
| `py_compile` supervisor.py | PASS |
| `unittest` supervisor 183개 테스트 | PASS (1.158s) |
| `git diff --check` 변경 파일 | PASS |

## 수정 확인 (코드 직접 열람)

| ID | 위치 | 내용 | 확인 |
|---|---|---|---|
| P1 | supervisor.py:2659 | `_prepare_runtime_surfaces` 루프에 `raw.jsonl` 없음 | ✓ |
| P2 | supervisor.py:189 | `_last_dispatch_selection_key = ""` 멤버 선언 | ✓ |
| P2 | supervisor.py:1392–1393 | `dispatch_selection_key != _last_dispatch_selection_key` 조건부 emit | ✓ |
| 기존 dispatch_selection 테스트 | — | payload shape 유지, 3개 기존 테스트 통과 | ✓ |

## 확인하지 않은 항목

- Playwright / E2E / controller-smoke: UI 계약 미변경, 실행 불필요
- live runtime start/stop: 이번 변경은 로그 초기화 경로만 수정
- Task 2 (P8/P11/P13/P16/P18), Task 3 (P3/P4), Task 4-C/D (P5/P7): 아직 미수정

## 현재 shipped truth (누적)

**Task 1 (완료):** P6/P9/P10/P14/P15/P17 — 단순 버그 6건
**Task 4-A/B (완료):** P1/P2 — 장기 실행 안정성 2건
- 재시작해도 `raw.jsonl` 보존 → 중복 핸드오프 탐지 유지
- `dispatch_selection` 이벤트 중복 억제 → events.jsonl 무한 증가 차단

## 남은 미수정 이슈

| 우선순위 | ID | 태스크 | 내용 |
|---|---|---|---|
| 🔴 성능 | P3, P4 | Task 3 | SHA/raw.jsonl 매 폴 재연산 캐시 |
| 🟠 로직 | P8, P11 | Task 2 | 스폰 실패 정리 · post-accept 보호 |
| 🟠 로직 | P13, P16, P18 | Task 2 | 레거시 cleanup · 하드코딩 키 · 타입 방어 |
| 🟠 경쟁 조건 | P5, P7 | Task 4-C/D | 동시 start 직렬화 · TOCTOU 재확인 |

## 다음 슬라이스 권고

**Task 2 (P8/P11/P13/P16/P18)** — 로직 교정 5건.
Task 3(캐싱)보다 로직 오류를 먼저 닫는 것이 안전하다.
Task 4-C/D(경쟁 조건)는 fcntl 잠금이 필요해 변경 범위가 크므로 마지막에 처리.
