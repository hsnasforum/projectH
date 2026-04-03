# 2026-04-03 document-search search-only response-detail preview-card second-card ordinal-prefix regression coverage

**범위**: search-only response detail second card의 ordinal prefix 회귀 검증 추가

---

## 변경 파일

- `e2e/tests/web-smoke.spec.mjs` — search-only 시나리오에서 response detail panel second card `.search-preview-name` nth(1)에 "2. memo.md" ordinal prefix 포함 assertion 1건 추가

---

## 사용 skill

- `work-log-closeout`

---

## 변경 이유

search-only response detail first-card는 이전 라운드에서 `1. budget-plan.md` ordinal prefix로 잠겼지만, second-card는 bare `memo.md`만 잠기고 있었음. UI 코드에서 `(idx + 1) + ". " + fileName`으로 렌더링하므로 second-card도 `2. memo.md`까지 직접 잠가야 ordinal prefix regression이 양쪽 카드에서 모두 보장됨.

---

## 핵심 변경

1. `e2e/tests/web-smoke.spec.mjs` — search-only 시나리오 response detail panel:
   - `page.locator("#response-search-preview .search-preview-name").nth(1)` → `toContainText("2. memo.md")` assertion 추가 (line 253)

---

## 검증

- `git diff --check -- e2e/tests/web-smoke.spec.mjs` — 통과
- `make e2e-test` — 17 passed (2.5m)
- `python3 -m unittest -v tests.test_web_app` — 미실행 (server 로직 변경 없음)

---

## 남은 리스크

- smoke 시나리오 수 17 변동 없음
- docs 동기화 불필요 (ordinal prefix는 아직 docs에서 명시적으로 기술되지 않았지만, 현재 wording과 충돌하지 않음)
- search-only response detail panel의 both cards ordinal prefix가 이제 전부 잠김. search-only response detail ordinal prefix family 닫힘.
- 같은 ordinal prefix coverage 공백: search-only transcript both cards, search-plus-summary response detail/transcript both cards. 다음 슬라이스 후보.
