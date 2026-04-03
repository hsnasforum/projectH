# 2026-04-03 document-search preview-card full-path-tooltip exact-path smoke tightening

**범위**: preview-card title tooltip smoke assertions를 regex에서 exact path로 강화

---

## 변경 파일

- `e2e/tests/web-smoke.spec.mjs` — 4 surfaces × 2 cards의 title tooltip assertions를 ending-regex → exact path 상수로 교체

---

## 사용 skill

- `work-log-closeout`

---

## 변경 이유

기존 smoke는 preview-card title tooltip을 `/.*\/budget-plan\.md$/` / `/.*\/memo\.md$/` ending regex로만 확인했기 때문에, tooltip에 예상과 다른 prefix가 붙거나 전혀 다른 path가 끼어도 assertion이 통과할 수 있었습니다.

핸드오프에서는 `searchFixtureBudgetPath` / `searchFixtureMemoPath` (절대 경로 상수)를 재사용하라고 했지만, 실제 shipped UI behavior를 검증한 결과:
- folder selection 시나리오에서 `sr.path`는 서버가 `uploaded_search_files`의 `relative_path`를 그대로 사용하므로 `picked-search-folder/budget-plan.md` 형태의 상대 경로입니다.
- `core/agent_loop.py:770` — `FileSearchResult(path=relative_path, ...)`

따라서 `searchFolderRelBudgetPath` / `searchFolderRelMemoPath` 상대 경로 상수를 새로 정의하여 실제 렌더링 값과 exact match하도록 수정했습니다.

---

## 핵심 변경

1. `searchFolderRelBudgetPath`, `searchFolderRelMemoPath` 상수 추가 (`path.basename(searchFixtureDir) + "/..."`)
2. search-plus-summary response detail: 2 assertions → exact relative path
3. search-plus-summary transcript: 2 assertions → exact relative path
4. search-only response detail: 2 assertions → exact relative path
5. search-only transcript: 2 assertions → exact relative path
6. 총 8줄 교체, 2줄 추가 (net +2)
7. ordered label, match badge, snippet, hidden-body/copy-button gating, scenario count(17) 변동 없음

---

## 검증

- `git diff --check -- e2e/tests/web-smoke.spec.mjs` — 통과
- `searchFolderRelBudgetPath|searchFolderRelMemoPath` grep — 10건 (2 정의 + 8 사용)
- stale `toHaveAttribute("title", /.*\\/` regex — 0건
- `make e2e-test` — 17/17 통과 (2.8m)
- `python3 -m unittest -v tests.test_web_app` — 미실행 (test-only smoke-tightening 라운드, server 로직 변경 없음)

---

## 남은 리스크

- preview-card title tooltip family의 exact-path smoke tightening 완료
- 핸드오프 가정 (절대 경로)과 실제 shipped behavior (folder selection = 상대 경로)의 차이를 발견 후 실제 behavior에 맞춤
- smoke 시나리오 수 17 변동 없음
- 다음 슬라이스는 새 property family로 이동 가능
