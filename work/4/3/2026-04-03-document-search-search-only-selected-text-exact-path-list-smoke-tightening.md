# 2026-04-03 document-search search-only selected-text exact-path-list smoke tightening

**범위**: folder-search(search-only) 시나리오의 `#selected-text` assertion을 exact path list로 강화

---

## 변경 파일

- `e2e/tests/web-smoke.spec.mjs` — `#selected-text` assertion 1줄 교체

---

## 사용 skill

- 없음 (handoff 직접 구현)

---

## 변경 이유

기존 smoke는 search-only의 selected path panel을 `toContainText("budget-plan.md")`로만 확인했기 때문에, panel에 예상과 다른 추가 경로가 섞이거나 순서가 바뀌어도 assertion이 통과할 수 있었습니다.

shipped UI는 `renderSelected()`가 `items.join("\n")`으로 exact multiline text를 렌더링하므로, 이 contract을 `toHaveText()`로 잠그는 것이 가장 작은 current-risk reduction입니다.

이전 라운드에서 search-plus-summary의 동일 assertion(line 202)은 이미 exact로 전환되었고, 이번 라운드는 search-only(line 260)를 마저 닫는 same-family 마무리입니다.

---

## 핵심 변경

1. `await expect(page.locator("#selected-text")).toContainText("budget-plan.md")` → `await expect(page.locator("#selected-text")).toHaveText(searchFolderRelBudgetPath + "\n" + searchFolderRelMemoPath)`
2. 1줄 교체 (net 0)
3. `#selected-text` assertion 2건 모두 now exact (`toHaveText`)
4. `toContainText("budget-plan.md")` — 파일 전체에서 0건
5. preview-card assertions, meta assertions, scenario count(17) 변동 없음

---

## 검증

- `git diff --check -- e2e/tests/web-smoke.spec.mjs` — 통과
- stale `toContainText("budget-plan.md")` — 파일 전체 0건
- `#selected-text` assertions — 2건 모두 `toHaveText()` (line 202, 260)
- `make e2e-test` — 17/17 통과 (2.6m)
- `python3 -m unittest -v tests.test_web_app` — 미실행 (test-only smoke-tightening 라운드, server 로직 변경 없음)

---

## 남은 리스크

- search-only `#selected-text` exact path list smoke tightening 완료
- `#selected-text` family는 search-plus-summary, search-only 모두 exact로 닫힘
- smoke 시나리오 수 17 변동 없음
- unrelated dirty worktree는 이번 라운드에서 건드리지 않음
