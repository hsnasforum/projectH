# verify: 2026-05-21 pipeline launcher Task 1 bugfixes

## 대상 work
`work/5/21/2026-05-21-pipeline-launcher-task1-bugfixes.md`

## 검증 결과: READY (Task 1 범위)

## 재실행 검증

| 검사 | 결과 |
|---|---|
| `py_compile` supervisor / cli / automation_health | PASS |
| `unittest` 3개 모듈 260개 테스트 | PASS (1.232s) |
| `git diff --check` 변경 파일 | PASS |

## 수정 확인 (코드 직접 열람)

| ID | 위치 | 내용 | 확인 |
|---|---|---|---|
| P9 | cli.py:486 | `tmux_session` 체크 `"ok" if exists else "warn"` | ✓ |
| P17 | automation_health.py:244 | `automation_incident_family` 끝 `return ""` | ✓ |
| P10 | supervisor.py:373–380 | `KeyError → lane_command_override_invalid 이벤트 + ""` | ✓ |
| P15 | supervisor.py:874–878 | `except Exception as exc → control_seq_age_error 이벤트` | ✓ |
| P6 | supervisor.py:1971–1976 | `atomic_write_text()` 사용 (schema.py:290 정의 확인) | ✓ |
| P14 | supervisor.py ~1875 | 단일 항목 루프 제거, 직접 처리로 대체 | ✓ (컴파일 통과) |

## 확인하지 않은 항목

- Playwright / E2E / controller-smoke: Task 1은 runtime 내부 로직만 변경 — UI 계약 미변경, 실행 불필요
- live runtime start/stop: 현재 환경에서 tmux 세션 없음 — 수행하지 않음
- Task 2–4 (P1/P2/P3/P4/P5/P7/P8/P11/P13/P16/P18): 이번 라운드 범위 밖

## 현재 shipped truth

- doctor tmux 체크가 세션 부재 시 `warn`을 정직하게 반환 (P9)
- 알 수 없는 automation reason code가 빈 family로 반환되어 메트릭 노이즈 감소 (P17)
- lane override format 오류가 미해석 템플릿 셸 전달 없이 이벤트로 기록됨 (P10)
- compat 텍스트 파일 쓰기가 원자적 (P6)
- control_seq_age 예외가 조용히 사라지지 않고 이벤트로 관찰 가능 (P15)

## 남은 리스크

- **P1 (고위험)**: raw.jsonl이 재시작 시 초기화됨 — 중복 핸드오프 탐지 실패 가능. Task 4-A에서 수정 예정.
- **P2 (고위험)**: events.jsonl에 dispatch_selection 이벤트가 매초 기록 — 장기 실행 시 무한 증가. Task 4-B에서 수정 예정.
- P3, P4 (성능): SHA/raw.jsonl 매 폴 재연산 — Task 3에서 캐싱 예정.
- P5, P7 (경쟁 조건): 동시 start / TOCTOU — Task 4-C/D에서 수정 예정.
- P8, P11, P13, P16, P18 (로직): Task 2에서 수정 예정.

## 다음 슬라이스

Task 4-A (P1) + Task 4-B (P2) — raw.jsonl 보존 + dispatch_selection 중복 억제.
고위험 2건을 먼저 닫는 것이 Task 2(로직) · Task 3(성능) 순서보다 우선.
