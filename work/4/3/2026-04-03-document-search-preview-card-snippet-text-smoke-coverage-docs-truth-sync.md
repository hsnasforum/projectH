# 2026-04-03 document-search preview-card snippet-text smoke-coverage docs truth sync

**범위**: preview-card snippet smoke coverage wording을 현재 truth에 맞게 docs 동기화

---

## 변경 파일

- `README.md` — scenario 3/4 smoke 요약에서 "snippet visibility" → "snippet text content", "content snippet visibility" → "content snippet text"
- `docs/ACCEPTANCE_CRITERIA.md` — 동일 패턴 수정 (scenario 3/4 smoke 요약)
- `docs/MILESTONES.md` — 동일 패턴 수정 (Milestone 3 smoke 요약)
- `docs/TASK_BACKLOG.md` — 동일 패턴 수정 (item 12/13 smoke 요약)

---

## 사용 skill

- `work-log-closeout`

---

## 변경 이유

preview-card snippet-text regression coverage가 search-plus-summary와 search-only 양쪽 모두 response detail/transcript의 both cards에서 direct text assertion으로 전부 닫혔음에도, docs의 smoke coverage 요약은 여전히 "snippet visibility" 수준에 머물러 있었음. 실제 smoke suite는 이제 visibility뿐 아니라 직접 text content까지 검증하므로, docs가 과소서술하고 있었음.

---

## 핵심 변경

1. 4개 문서에서 "snippet visibility" → "snippet text content" (search-plus-summary scenario)
2. 4개 문서에서 "content snippet visibility" → "content snippet text" (search-only scenario)

---

## 검증

- `git diff --check -- README.md docs/ACCEPTANCE_CRITERIA.md docs/MILESTONES.md docs/TASK_BACKLOG.md` — 통과
- `rg "snippet visibility" README.md docs/ACCEPTANCE_CRITERIA.md docs/MILESTONES.md docs/TASK_BACKLOG.md` — 0건 (stale wording 잔존 없음)
- `rg "snippet text" README.md docs/ACCEPTANCE_CRITERIA.md docs/MILESTONES.md docs/TASK_BACKLOG.md` — 4개 문서 모두 올바르게 반영
- `make e2e-test` — 미실행 (docs-only 변경, 테스트 코드 수정 없음)
- `python3 -m unittest -v tests.test_web_app` — 미실행 (server 로직 변경 없음)

---

## 남은 리스크

- smoke 시나리오 수 17 변동 없음
- `docs/PRODUCT_SPEC.md`, `docs/NEXT_STEPS.md`는 generic "content snippet" 수준으로 already truthful하여 이번 라운드에서 변경하지 않았음
- preview-card snippet-text family와 docs truth sync가 모두 닫힘. 다음 슬라이스는 새 property family(tooltip/badge/item-count 등)로 이동 가능.
