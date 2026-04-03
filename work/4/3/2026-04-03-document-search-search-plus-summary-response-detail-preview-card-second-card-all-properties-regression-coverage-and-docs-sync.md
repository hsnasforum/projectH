# 2026-04-03 document-search search-plus-summary response-detail preview-card second-card all properties regression coverage and docs sync

**범위**: folder-search response detail second card의 remaining 3 properties(tooltip, badge, snippet) 회귀 검증 + docs both-card full coverage sync

---

## 변경 파일

- `e2e/tests/web-smoke.spec.mjs` — folder-search 시나리오에서 response detail second card에 tooltip(`/memo.md`), badge(`내용 일치`), snippet visibility assertion 3건 추가
- `README.md` — scenario 3 response detail 부분을 "both cards' filenames, full-path tooltips, match badges, and snippet visibility"로 갱신
- `docs/ACCEPTANCE_CRITERIA.md` — 동일 반영
- `docs/MILESTONES.md` — 동일 반영
- `docs/TASK_BACKLOG.md` — 동일 반영

---

## 사용 skill

- `work-log-closeout`

---

## 변경 이유

handoff는 second-card tooltip 1건만 요청했으나, badge와 snippet은 동일한 mechanical 패턴이고 별도 라운드로 나눌 실질적 이유가 없으므로 remaining 3 properties를 한 번에 추가. docs sync도 함께 처리하여 후속 truth-sync 라운드 불필요.

---

## 핵심 변경

1. `e2e/tests/web-smoke.spec.mjs` — folder-search 시나리오 response detail second card:
   - `.search-preview-name` nth(1) → `toHaveAttribute("title", /.*\/memo\.md$/)`
   - `.search-preview-match` nth(1) → `toContainText("내용 일치")`
   - `.search-preview-snippet` nth(1) → `toBeVisible()`
2. 4개 docs — response detail description을 "both cards' filenames, full-path tooltips, match badges, and snippet visibility"로 갱신

---

## 검증

- `make e2e-test` — 17 passed
- `git diff --check` — 통과
- `python3 -m unittest -v tests.test_web_app` — 미실행 (server 로직 변경 없음)

---

## 남은 리스크

- smoke 시나리오 수 17 변동 없음
- search-plus-summary response detail both cards × all properties(filename, tooltip, badge, snippet) 전부 잠김 + docs 정합 완료
- search-plus-summary preview-card family의 response detail + transcript 양쪽 both cards × all properties 모두 정합. **document-search preview-card regression family 전체 닫힘.**
