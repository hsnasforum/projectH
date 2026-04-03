# 2026-04-03 document-search selected-copy exact-path-list smoke tightening

**범위**: search-only 시나리오의 selected-copy clipboard assertion을 exact path list로 강화

---

## 변경 파일

- `e2e/tests/web-smoke.spec.mjs` — clipboard assertion 1줄 교체

---

## 사용 skill

- `work-log-closeout`

---

## 변경 이유

기존 smoke는 selected-copy 클릭 후 clipboard를 `expect(clipboardText).toContain("budget-plan.md")`로만 확인했기 때문에, clipboard에 예상과 다른 추가 경로가 섞이거나 순서가 바뀌어도 assertion이 통과할 수 있었습니다.

shipped UI는 `renderSelected()`가 `selected_source_paths`를 줄바꿈으로 join하고, `copyTextValue(selectedText.textContent, ...)`로 그대로 복사하므로, clipboard 값은 exact relative path list입니다.

---

## 핵심 변경

1. `expect(clipboardText).toContain("budget-plan.md")` → `expect(clipboardText).toBe(searchFolderRelBudgetPath + "\n" + searchFolderRelMemoPath)`
2. 1줄 교체 (net 0)
3. selected-copy visibility, click, notice assertion 변동 없음
4. preview-card assertions, scenario count(17) 변동 없음

---

## 검증

- `git diff --check -- e2e/tests/web-smoke.spec.mjs` — 통과
- stale `toContain("budget-plan.md")` clipboard assertion — 0건
- `make e2e-test` — 17/17 통과 (2.7m)
- `python3 -m unittest -v tests.test_web_app` — 미실행 (test-only smoke-tightening 라운드, server 로직 변경 없음)

---

## 남은 리스크

- selected-copy clipboard exact path list smoke tightening 완료
- smoke 시나리오 수 17 변동 없음
- preview-card family (ordered label, match badge, full-path tooltip)와 selected-copy clipboard exactness가 모두 aligned
- 다음 슬라이스는 새 property family로 이동 가능
