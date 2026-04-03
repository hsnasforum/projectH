# 2026-04-03 document-search preview-card match-badge-snippet regression coverage

**범위**: preview card의 match-type badge와 content snippet contract 회귀 검증 추가 + docs truth-sync

---

## 변경 파일

- `e2e/tests/web-smoke.spec.mjs` — search-only 시나리오에서 response detail + transcript 양쪽의 첫 card에 `.search-preview-match` 텍스트("파일명 일치")와 `.search-preview-snippet` visibility assertion 추가 (4건)
- `README.md` — smoke scenario 4번에 match-type badge + snippet visibility coverage 반영
- `docs/ACCEPTANCE_CRITERIA.md` — search-only bullet에 동일 반영
- `docs/MILESTONES.md` — search-only smoke 항목에 동일 반영
- `docs/TASK_BACKLOG.md` — 완료 항목 13번에 동일 반영

---

## 사용 skill

- `work-log-closeout`

---

## 변경 이유

root docs와 PRODUCT_SPEC은 preview card가 match-type badge와 content snippet을 보여 준다고 적고, 구현도 양쪽 renderer에서 `search-preview-match`와 `search-preview-snippet`을 렌더링하지만, Playwright smoke는 이 두 요소를 직접 잠그지 않았음. preview-card contract의 마지막 current-risk였음.

---

## 핵심 변경

1. `e2e/tests/web-smoke.spec.mjs` — search-only 시나리오:
   - response detail: `.search-preview-match` 첫 번째 → "파일명 일치" 포함 확인
   - response detail: `.search-preview-snippet` 첫 번째 → visible 확인
   - transcript: 동일 2건
2. 4개 docs — smoke 설명에 "match-type badge (`파일명 일치` / `내용 일치`) plus content snippet visibility" 추가

---

## 검증

- `make e2e-test` — 17 passed
- `git diff --check -- e2e/tests/web-smoke.spec.mjs README.md docs/ACCEPTANCE_CRITERIA.md docs/MILESTONES.md docs/TASK_BACKLOG.md` — 통과

---

## 남은 리스크

- smoke 시나리오 수 17 변동 없음 (기존 시나리오 안에 assertion만 추가)
- preview-card contract(filename, tooltip, badge, snippet)의 code/regression/docs가 모두 정합한 상태. same-family current-risk 닫힘.
