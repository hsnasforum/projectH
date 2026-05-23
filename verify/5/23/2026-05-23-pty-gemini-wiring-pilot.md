# verify: 2026-05-23 PtyAdapter Gemini wiring pilot (2159)

## 대상 work
`work/5/23/2026-05-23-pty-gemini-wiring-pilot.md`

## 검증 결과: READY → NEXT_CONTROL_DISPATCHED (live smoke 미실행 명시)

### advisory 소비 기록 (2026-05-23)
- advisory_request#2161 (pty_smoke_pending_next_slice_triage) → advisory_advice#2162 소비 완료.
- CONTROL_SEQ 2163 발행: `.pipeline/implement_handoff.md` STATUS=verify ROLE=verify OWNER=Claude.
- 다음 라운드: pipeline STARTING 완료 후 events.jsonl/status.json/health/watcher log 관찰 → live smoke pass/fail 확정.
- commit/revert 결정은 live smoke 결과 기록 후.

---

## 코드 확인

| 항목 | 위치 | 확인 |
|---|---|---|
| `PtyLaneBridge` 클래스 추가 | `watcher_pty_adapter.py` | ✓ |
| `register / capture / send / teardown / is_registered` | `watcher_pty_adapter.py` | ✓ |
| `pty_pilot_lane` 플래그 읽기 + 조건부 bridge 생성 | `watcher_core.py __init__` | ✓ |
| Gemini pane target → PtyLaneBridge capture 인터셉션 | `watcher_core.py` (3개 람다) | ✓ |
| Codex / Claude capture 람다 **변경 없음** | `watcher_core.py` | ✓ |
| `"pty_pilot_lane": ""` (기본값) | `.pipeline/config/runtime_policy.json` | ✓ |
| `.pipeline/README.md` pty_pilot_lane 문서화 | `.pipeline/README.md` | ✓ |

## 회귀 검증

| 검사 | 결과 |
|---|---|
| `python3 -m py_compile` (4개 파일) | PASS |
| `tests.test_watcher_pty_adapter` (7+3=10개) | **PASS** |
| `tests.test_watcher_core.PtyPilotWiringTest` (2개) | **PASS** |
| 전체 suite 570개 | **PASS (0 FAIL, 0 ERROR)** |
| `git diff --check` | PASS |
| `policy key OK: ''` | PASS |

## wiring 동작 검증

| 조건 | 동작 |
|---|---|
| `pty_pilot_lane == ""` (기본) | `_pty_bridge = None`, tmux capture 그대로 |
| `pty_pilot_lane == "Gemini"` | Gemini target → PtyLaneBridge.capture(), 미등록 target → tmux fallback |
| Codex / Claude target | 항상 tmux capture (브릿지 영향 없음) |

---

## 남은 리스크 (명시)

| 항목 | 상태 |
|---|---|
| live Gemini PTY smoke (`gemini --yolo` child) | **미실행** |
| 장시간 PTY 수명 (backpressure, deque 포화) | 미검증 |
| attach/debug UX (PTY 내 터미널 크기 전파) | 미검증 |

live smoke는 `runtime_policy.json`에서 `"pty_pilot_lane": "Gemini"`로 설정 후 별도 파이프라인 실행으로 검증 필요.

---

## A3 Step 9-10 수치

| 항목 | 결과 |
|---|---|
| `watcher_pty_adapter.py` | +PtyLaneBridge (현재 총 ~330줄) |
| `watcher_core.py` | 조건부 bridge 초기화 추가 |
| 전체 테스트 | 560 → **570개** |
| 기존 소스 회귀 | 없음 |
