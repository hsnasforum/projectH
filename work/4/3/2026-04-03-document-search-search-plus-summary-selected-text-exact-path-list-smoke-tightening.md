# 2026-04-03 document-search search-plus-summary selected-text exact-path-list smoke tightening

**범위**: folder-search(search-plus-summary) 시나리오의 `#selected-text` assertion을 exact path list로 강화

---

## 변경 파일

- `e2e/tests/web-smoke.spec.mjs` — `#selected-text` assertion 1줄 교체

---

## 사용 skill

- `work-log-closeout`

---

## 변경 이유

기존 smoke는 search-plus-summary의 selected path panel을 `toContainText("budget-plan.md")`로만 확인했기 때문에, panel에 예상과 다른 추가 경로가 섞이거나 순서가 바뀌어도 assertion이 통과할 수 있었습니다.

shipped UI는 `renderSelected()`가 `items.join("\n")`으로 exact multiline text를 렌더링하므로, 이 contract을 `toHaveText()`로 잠그는 것이 가장 작은 current-risk reduction입니다.

---

## 핵심 변경

1. `await expect(page.locator("#selected-text")).toContainText("budget-plan.md")` → `await expect(page.locator("#selected-text")).toHaveText(searchFolderRelBudgetPath + "\n" + searchFolderRelMemoPath)`
2. 1줄 교체 (net 0)
3. search-only의 `#selected-text` assertion(line 260)은 이번 범위 밖 — 유지
4. preview-card assertions, meta assertions, scenario count(17) 변동 없음

---

## 검증

- `git diff --check -- e2e/tests/web-smoke.spec.mjs` — 통과
- stale `selected-text).toContainText("budget-plan.md")` — search-plus-summary에서 0건 (search-only 1건은 범위 밖 유지)
- `make e2e-test` — 17/17 통과 (2.5m)
- `python3 -m unittest -v tests.test_web_app` — 미실행 (test-only smoke-tightening 라운드, server 로직 변경 없음)

---

## 남은 리스크

- search-plus-summary `#selected-text` exact path list smoke tightening 완료
- search-only `#selected-text`(line 260)는 아직 `toContainText` — 다만 같은 시나리오의 clipboard `toBe()` assertion이 동일 DOM text를 간접적으로 잠그고 있음
- smoke 시나리오 수 17 변동 없음
