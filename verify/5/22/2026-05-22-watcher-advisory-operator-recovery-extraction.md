# verify: 2026-05-22 watcher advisory/operator recovery extraction (2154)

## 대상 work
`work/5/22/2026-05-22-watcher-advisory-operator-recovery-extraction.md`

## 검증 결과: READY

---

## 코드 확인

| 항목 | 위치 | 확인 |
|---|---|---|
| `StaleAdvisoryRecovery` 클래스 | `watcher_recovery.py` | ✓ |
| `OperatorRetrageTracker` / `OperatorRetriageTracker` alias | `watcher_recovery.py` | ✓ |
| advisory recovery 본문 → delegation wrapper | `watcher_core.py:2077–2393` | ✓ |
| operator retriage 본문 → delegation wrapper | `watcher_core.py:1683–1802` | ✓ |
| advisory/operator 상태 변수 8개 → 새 클래스로 이동 | `watcher_core.py __init__` | ✓ |
| 새 테스트 파일 | `tests/test_watcher_recovery.py` (245줄) | ✓ |

## 회귀 검증

| 검사 | 결과 |
|---|---|
| `python3 -m py_compile` (3개 파일) | PASS |
| `tests.test_watcher_recovery` | PASS |
| 전체 suite 560개 | **PASS (0 FAIL, 0 ERROR)** |
| `git diff --check` | PASS |

---

## A3 추출 진행 상황

| 단계 | 모듈 | 줄수 | 상태 |
|---|---|---|---|
| Step 1–5 | control_signals, job_state, artifact_scanner, runtime_exporter, module-fn | — | ✓ |
| Step 6 | `watcher_status_writer.py` | 139줄 | ✓ |
| Step 7 | `watcher_lane_status.py` | 62줄 | ✓ |
| **Step 8** | **`watcher_recovery.py`** | **527줄** | **✓** |

`watcher_core.py`: 4498 → 4130 → **3858줄** (총 −640)
전체 테스트: 549 → **560개** (+11)
