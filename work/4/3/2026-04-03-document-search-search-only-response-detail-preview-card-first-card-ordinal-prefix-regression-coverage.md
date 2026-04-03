# 2026-04-03 document-search search-only response-detail preview-card first-card ordinal-prefix regression coverage

**범위**: search-only response detail first card의 ordinal prefix 회귀 검증 추가

---

## 변경 파일

- `e2e/tests/web-smoke.spec.mjs` — search-only 시나리오에서 response detail panel first card `.search-preview-name` first에 "1. budget-plan.md" ordinal prefix 포함 assertion 1건 추가

---

## 사용 skill

- `work-log-closeout`

---

## 변경 이유

UI 코드(`app/static/app.js`)에서 preview card filename은 `(idx + 1) + ". " + fileName`으로 ordinal prefix와 함께 렌더링되지만, smoke에서는 bare filename `budget-plan.md`만 `toContainText`로 잠기고 있었음. ordinal prefix가 빠지거나 순서가 바뀌어도 기존 assertion만으로는 잡히지 않으므로, `1. budget-plan.md` full visible text를 직접 잠글 필요가 있었음.

---

## 핵심 변경

1. `e2e/tests/web-smoke.spec.mjs` — search-only 시나리오 response detail panel:
   - `page.locator("#response-search-preview .search-preview-name").first()` → `toContainText("1. budget-plan.md")` assertion 추가 (line 247)

---

## 검증

- `git diff --check -- e2e/tests/web-smoke.spec.mjs` — 통과
- `make e2e-test` — 17 passed (2.2m)
- `python3 -m unittest -v tests.test_web_app` — 미실행 (server 로직 변경 없음)

---

## 남은 리스크

- smoke 시나리오 수 17 변동 없음
- docs 동기화 불필요 (ordinal prefix는 아직 docs에서 명시적으로 기술되지 않았지만, 현재 wording과 충돌하지 않음)
- 같은 ordinal prefix coverage 공백: search-only response detail second-card, search-only transcript both cards, search-plus-summary response detail/transcript both cards. 다음 슬라이스 후보.
