# history-card entity-card zero-strong-slot reload answer-mode wording sync

날짜: 2026-04-07

## 변경 파일

- `e2e/tests/web-smoke.spec.mjs` — scenario 35 title wording 수정 ("downgraded verification badge" → "설명 카드 answer-mode badge와 설명형 단일 출처 verification label")
- `README.md` — scenario 35 설명 wording 수정 ("downgraded verification badge(설명 카드)" → "`설명 카드` answer-mode badge")

## 사용 skill

- 없음

## 변경 이유

- `설명 카드`는 response answer-mode badge이지 verification-strength badge가 아님. 이전 라운드에서 scenario title과 README 설명에 "downgraded verification badge"로 잘못 기재됨
- `docs/ACCEPTANCE_CRITERIA.md`, `docs/MILESTONES.md`, `docs/TASK_BACKLOG.md`는 이미 implementation wording과 맞았으므로 수정 불필요

## 핵심 변경

- scenario title: `downgraded verification badge와 verification label` → `설명 카드 answer-mode badge와 설명형 단일 출처 verification label`
- README: `downgraded verification badge(설명 카드)` → `` `설명 카드` answer-mode badge``

## 검증

- `git diff --check` — 통과
- `cd e2e && npx playwright test tests/web-smoke.spec.mjs -g "history-card entity-card zero-strong-slot 다시 불러오기 후 설명 카드 answer-mode badge와 설명형 단일 출처 verification label이 유지됩니다" --reporter=line` — 1 passed (6.7s)
- scenario count 변경 없음 (35 유지)

## 남은 리스크

- 없음 (wording-only sync)
