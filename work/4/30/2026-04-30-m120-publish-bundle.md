# 2026-04-30 M120 publish bundle

## 이번 라운드 범위

operator_retriage CONTROL_SEQ 1545 → 1546.
`commit_push_bundle_authorization + pr_creation_gate` 처리.

## 실행 내용

- operator_retriage: orphaned JS/E2E 범위 결정이 실제 operator 차단 요인이 아님을 확인 (controller_server 28 tests PASS, JS syntax PASS).
- orphaned `attentionOperatorEligible()` fix + E2E smoke를 별도 커밋으로 `feat/m119-injection-correction-loop`에 먼저 커밋 (option B: 이력 분리).
- 신규 브랜치 `feat/m120-injection-correction-reliability-filter` (base: `feat/m119-injection-correction-loop`) 생성.
- M120 변경 7개 파일 커밋.
- push → `origin/feat/m120-injection-correction-reliability-filter`.
- draft PR #114 생성 (base: `feat/m119-injection-correction-loop`).

## 커밋 결과

| 커밋 | 브랜치 | 내용 |
|------|--------|------|
| `ddacf60` | `feat/m119-injection-correction-loop` | fix(controller): derive operator eligibility from health and control state |
| `155901a` | `feat/m120-injection-correction-reliability-filter` | feat(preferences): injection-correction reliability filter (M120) |

## PR 스택

| PR | 브랜치 | base | 상태 |
|----|--------|------|------|
| #113 | `feat/m119-injection-correction-loop` | `feat/m118-injected-count-api-exposure` | draft |
| #114 | `feat/m120-injection-correction-reliability-filter` | `feat/m119-injection-correction-loop` | draft |

URL: https://github.com/hsnasforum/projectH/pull/114

## 검증 (이번 라운드 직접 실행)

| 체크 | 결과 |
|------|------|
| `python3 -m unittest -v tests.test_controller_server` | PASS — 28개 |
| JS syntax check (`node --check controller/js/cozy.js`) | PASS |
| `python3 -m unittest -v tests.test_preference_handler` | PASS — 25개 |
| `python3 -m unittest -v tests.test_preference_store` | PASS — 34개 |

## 남은 리스크

- PR #113, #114 draft — pr_merge_gate operator 대기
- M119 Axis 2 (injection_correction_rate UI 표시) 미구현
- M121 미정의 — TASK_BACKLOG에 다음 슬라이스 없음
