STATUS: verified
CONTROL_SEQ: 1545
BASED_ON_WORK: work/4/30/2026-04-30-m120-axis1-reliability-filter.md
VERIFIED_BY: Claude (verify owner)
NEXT_CONTROL: operator_request.md CONTROL_SEQ 1545

---

# 2026-04-30 M120 Axis 1 injection correction reliability filter — verify

## 이번 라운드 범위

CONTROL_SEQ 1544 implement_handoff (m120_axis1_reliability_filter) 실행 결과.
work note 변경 범위: `storage/preference_utils.py`, `tests/test_preference_handler.py`, docs 5개 파일.

## 직접 실행 결과

| 체크 | 결과 |
|------|------|
| `python3 -m py_compile storage/preference_utils.py` | **PASS** |
| `python3 -m unittest -v tests.test_preference_handler` | **PASS — 25개** (M119 23개 → +2 M120 신규: demotes_high_injection_correction_rate, high_rate_overrides_explicit_reliability) |
| `python3 -m unittest -v tests.test_preference_store` | **PASS — 34개** (회귀 없음) |
| `git diff --check` (7개 M120 파일) | **PASS** |

## dirty tree 현황 (9개 파일) — 미커밋, 브랜치 `feat/m119-injection-correction-loop`

| 분류 | 파일 | 출처 |
|------|------|------|
| M120 Axis 1 | `storage/preference_utils.py` | `INJECTION_CORRECTION_THRESHOLD=0.25`, `INJECTION_MINIMUM_COUNT=3`, `_injection_correction_rate_exceeded()`, `enrich_preference_reliability()` / `is_highly_reliable_preference()` 우선 강등 |
| M120 Axis 1 | `tests/test_preference_handler.py` | 강등 케이스 2개 신규 |
| M120 docs | `docs/PRODUCT_SPEC.md` | M120 동작 반영 |
| M120 docs | `docs/ARCHITECTURE.md` | M120 동작 반영 |
| M120 docs | `docs/ACCEPTANCE_CRITERIA.md` | 강등 기준 추가 |
| M120 docs | `docs/MILESTONES.md` | M120 완료 항목 추가 |
| M120 docs | `docs/TASK_BACKLOG.md` | M120 완료 갱신 |
| **orphaned** | `controller/js/cozy.js` | `attentionOperatorEligible()` 신규 함수 + `buildOperatorAttention()` 수정 — work note 미커버 |
| **orphaned** | `e2e/tests/controller-smoke.spec.mjs` | "controller derives operator eligibility for health-only auth attention" 신규 smoke test — work note 미커버 |

M119 Axis 1: commit `84dc442`, PR #113 (draft, base: `feat/m118-injected-count-api-exposure`) — 이미 커밋 + push 완료.

## orphaned JS/E2E 변경 내용 요약

`controller/js/cozy.js` 변경:
- `attentionOperatorEligible(autonomy, nextAction, controlNeedsOperator, healthNeedsOperator)` 신규 함수
- `healthNeedsOperator` 또는 `controlNeedsOperator`가 true인 경우 `autonomy.operator_eligible: false` 저장값을 무시하고 eligible=true 도출
- `buildOperatorAttention()`에서 `operatorEligible` 계산을 이 함수로 위임

`e2e/tests/controller-smoke.spec.mjs`:
- "controller derives operator eligibility for health-only auth attention" — `automation_health: needs_operator`, `operator_eligible: false` payload에서 Eligible=true로 도출되는지 확인

기능상 M120과 독립적이며 work/4/30/ 어느 work note도 이 변경을 다루지 않음. 커밋 범위 결정은 operator 판단 필요.

## 검증 미실행 항목

- 전체 unittest 미실행 (preference helper/handler/store 중심 검증만 수행)
- `controller/js/cozy.js` orphaned 변경에 대한 controller_server 테스트 미실행
- 브라우저/E2E 미실행 — M120 Axis 1은 브라우저 계약 변경 없음; CI 위임
- commit, push, PR 생성 미수행

## 남은 리스크

- 9개 파일 미커밋 — M120 신규 브랜치 + PR 필요 (base: `feat/m119-injection-correction-loop`)
- orphaned JS/E2E 처리 결정 필요 (M120 커밋 합산 or 별도 커밋 or 별도 브랜치 분리)
- injection correction은 세션 단위 근사 신호 — 주입·교정 이벤트 시간 순서 미추적 (M119 carry-over)
- M121 정의 필요 (TASK_BACKLOG에 M121 미존재)
