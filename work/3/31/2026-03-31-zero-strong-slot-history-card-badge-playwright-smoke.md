# 2026-03-31 zero-strong-slot history-card badge Playwright smoke

## 변경 파일
- `e2e/tests/web-smoke.spec.mjs`

## 사용 skill
- 없음

## 변경 이유
- `.pipeline/codex_feedback.md`가 `STATUS: implement`로, zero-strong-slot entity-card의 downgraded verification badge가 browser history-card header에서도 올바르게 렌더링되는지 Playwright smoke로 확인하도록 지시.
- 기존 badge smoke는 strong verification entity-card만 검증하고, zero-strong-slot downgraded case는 다루지 않았음.

## 핵심 변경
- 기존 `web-search history card header badges` scenario에 4번째 card(zero-strong-slot entity-card) 추가
  - `answer_mode: "entity_card"`, `verification_label: "설명형 단일 출처"`, `source_roles: ["백과 기반"]`
  - 검증: answer-mode badge "설명 카드", verification badge "검증 중"(`ver-medium` — strong이 아님), source-role badge "백과 기반(높음)"(`trust-high`)
- scenario count 16 유지 (기존 scenario 확장, 새 scenario 아님)
- production 코드, service tests, docs 변경 없음

## 검증
- `make e2e-test`: 16 tests passed (3.8m)
- `git diff --check -- e2e/tests/web-smoke.spec.mjs`: 통과
- `python3 -m unittest -v tests.test_smoke`: 실행하지 않음
- `python3 -m unittest -v tests.test_web_app`: 실행하지 않음

## 남은 리스크
- dirty worktree가 여전히 넓음.
