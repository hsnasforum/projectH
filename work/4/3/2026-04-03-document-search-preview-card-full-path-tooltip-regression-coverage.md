# 2026-04-03 document-search preview-card full-path-tooltip regression coverage

**범위**: preview card filename의 full path tooltip contract를 직접 잠그는 regression coverage 추가

---

## 변경 파일

- `e2e/tests/web-smoke.spec.mjs` — search-only 시나리오에서 response detail과 transcript 양쪽의 `.search-preview-name` 첫 번째 요소에 `title` attribute가 full path (`/budget-plan.md`로 끝남)인지 검증하는 assertion 2건 추가
- `README.md` — smoke scenario 4번 설명에 full-path tooltip coverage 반영
- `docs/ACCEPTANCE_CRITERIA.md` — search-only bullet에 full-path tooltip coverage 반영

---

## 사용 skill

- `work-log-closeout`

---

## 변경 이유

root docs와 PRODUCT_SPEC은 preview card filename에 full path tooltip이 있다고 적고, 구현도 `nameEl.title = sr.path || ""`를 설정하지만, Playwright smoke는 `.search-preview-name` 텍스트만 확인하고 `title` 값을 직접 잠그지 않았음. 이 regression coverage 부재가 document-search preview-card contract의 마지막 current-risk였음.

---

## 핵심 변경

1. `e2e/tests/web-smoke.spec.mjs` — search-only 시나리오 안에서:
   - response detail box: `#response-search-preview .search-preview-name` 첫 번째 요소에 `toHaveAttribute("title", /.*\/budget-plan\.md$/)`
   - transcript: `lastAssistant.locator(".search-preview-name")` 첫 번째 요소에 동일 assertion
2. `README.md` — smoke scenario 4번에 "and full-path tooltip on preview card filenames in both response detail and transcript" 추가
3. `docs/ACCEPTANCE_CRITERIA.md` — search-only bullet에 동일 반영

---

## 검증

- `make e2e-test` — 17 passed
- `git diff --check -- e2e/tests/web-smoke.spec.mjs README.md docs/ACCEPTANCE_CRITERIA.md` — 통과

---

## 남은 리스크

- smoke 시나리오 수 17 변동 없음 (기존 시나리오 안에 assertion만 추가)
- preview-card full-path tooltip contract의 code/regression/docs가 모두 정합한 상태. same-family current-risk 닫힘.
