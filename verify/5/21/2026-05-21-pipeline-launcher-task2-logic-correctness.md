# verify: 2026-05-21 pipeline launcher Task 2 logic correctness

## 대상 work
`work/5/21/2026-05-21-pipeline-launcher-task2-logic-correctness.md`

## 검증 결과: READY (Task 2 범위)

## 재실행 검증

| 검사 | 결과 |
|---|---|
| `py_compile` supervisor.py / cli.py | PASS |
| `unittest` supervisor + cli 222개 테스트 | PASS (1.125s) |
| `git diff --check` 변경 파일 | PASS |

## 수정 확인 (코드 직접 열람)

| ID | 위치 | 내용 | 확인 |
|---|---|---|---|
| P11 | supervisor.py:1951 | `if post_accept:` — owner 조건 제거, 모든 레인 보호 | ✓ |
| P8 | supervisor.py:2904 | `except Exception: if spawned_lanes: kill_session()` | ✓ |
| P16 | cli.py:1138 | `re.search(r"^\s*...\s*skip until next version")` 동적 파싱, fallback `b"3\r"` | ✓ |
| P18 | cli.py:962 | `try: int(raw_control_seq) … except (TypeError, ValueError): -1` | ✓ |
| P13 | supervisor.py ~2580 | fingerprint 없는 경로 주석 문서화 (동작 변경 없음) | ✓ |

## 확인하지 않은 항목

- Playwright / E2E / controller-smoke: UI 계약 미변경
- live runtime start/stop: tmux 없는 환경
- Task 3 (P3/P4), Task 4-C/D (P5/P7): 아직 미수정

## 현재 shipped truth (누적)

| 라운드 | 완료 이슈 | 내용 |
|---|---|---|
| Task 1 | P6/P9/P10/P14/P15/P17 | 단순 버그 6건 |
| Task 4-A/B | P1/P2 | raw.jsonl 보존, events.jsonl 중복 억제 |
| Task 2 | P8/P11/P13/P16/P18 | 로직 교정 5건 |

## 남은 미수정 이슈

| 우선순위 | ID | 태스크 | 내용 |
|---|---|---|---|
| 🔴 성능 | P3 | Task 3 | raw.jsonl 400줄 매 폴 재파싱 캐시 |
| 🔴 성능 | P4 | Task 3 | SHA256 매 폴 재연산 캐시 |
| 🟠 경쟁 조건 | P5 | Task 4-C | 동시 start 직렬화 (fcntl flock) |
| 🟠 경쟁 조건 | P7 | Task 4-D | TOCTOU 재확인 |

## 다음 슬라이스 권고

**Task 3 (P3/P4)** — SHA/raw.jsonl 캐싱.
경쟁 조건(Task 4-C/D)보다 낮은 변경 범위로 즉각 성능 효과가 있으며,
캐시 키 설계가 이미 계획서에 구체적으로 작성되어 있어 Codex 실행 오류 가능성이 낮다.
