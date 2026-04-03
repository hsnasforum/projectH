# 2026-04-03 document-search preview-card ordered-label exact-text smoke tightening

**범위**: preview-card ordered-label smoke assertions를 exact visible text로 강화

---

## 변경 파일

- `e2e/tests/web-smoke.spec.mjs` — 4 surfaces × 2 cards의 ordered-label assertions를 `toContainText` → `toHaveText`로 교체

---

## 사용 skill

- `work-log-closeout`

---

## 변경 이유

기존 smoke는 `toContainText("1. budget-plan.md")` / `toContainText("2. memo.md")`로만 확인했기 때문에 unexpected prefix/suffix나 extra visible text가 끼어도 assertion이 통과할 수 있었습니다. shipped UI는 `(idx + 1) + ". " + fileName`으로 exact ordered label을 렌더링하므로, 이 contract을 exact text assertion으로 잠그는 것이 같은 family의 가장 작은 current-risk reduction입니다.

---

## 핵심 변경

1. search-plus-summary response detail: `toContainText("budget-plan.md")` + `toContainText("1. budget-plan.md")` → `toHaveText("1. budget-plan.md")` (card 1, card 2 동일 패턴)
2. search-plus-summary transcript: 동일 패턴
3. search-only response detail: 동일 패턴
4. search-only transcript: 동일 패턴
5. 총 16줄 삭제, 8줄 교체 (net -8줄)
6. full path tooltip, match badge, snippet, hidden-body/copy-button gating, scenario count(17) 변동 없음

---

## 검증

- `git diff --check -- e2e/tests/web-smoke.spec.mjs` — 통과
- `rg "toHaveText(\"1. budget-plan.md\")|toHaveText(\"2. memo.md\")" e2e/tests/web-smoke.spec.mjs` — 8건 (4 surfaces × 2 cards)
- stale `toContainText` on `.search-preview-name` — 0건
- `make e2e-test` — 17/17 통과
- `python3 -m unittest -v tests.test_web_app` — 미실행 (test-only smoke-tightening 라운드, server 로직 변경 없음)

---

## 남은 리스크

- preview-card ordered-label family의 exact-text smoke tightening 완료
- smoke 시나리오 수 17 변동 없음
- 다음 슬라이스는 새 property family로 이동 가능
