# 2026-04-03 document-search preview-card ordinal-prefix smoke-coverage docs truth sync

**범위**: preview-card ordinal prefix smoke coverage wording을 현재 truth에 맞게 docs 동기화

---

## 변경 파일

- `README.md` — scenario 3의 "both cards' filenames" → "both cards' ordered labels" (×2), scenario 4의 "preview card filenames" → "preview card ordered labels"
- `docs/ACCEPTANCE_CRITERIA.md` — 동일 패턴 수정
- `docs/MILESTONES.md` — 동일 패턴 수정
- `docs/TASK_BACKLOG.md` — 동일 패턴 수정

---

## 사용 skill

- `work-log-closeout`

---

## 변경 이유

preview-card ordinal prefix direct assertion family가 search-plus-summary와 search-only 양쪽 모두 response detail/transcript의 both cards에서 `1. budget-plan.md` / `2. memo.md`로 전부 닫혔음에도, docs의 smoke coverage 요약은 여전히 "filenames" 수준에 머물러 있었음. 실제 smoke suite는 이제 bare filename이 아니라 ordered visible label까지 직접 검증하므로, docs가 과소서술하고 있었음.

---

## 핵심 변경

1. 4개 문서에서 "both cards' filenames" → "both cards' ordered labels" (search-plus-summary scenario)
2. 4개 문서에서 "preview card filenames" → "preview card ordered labels" (search-only scenario)

---

## 검증

- `git diff --check -- README.md docs/ACCEPTANCE_CRITERIA.md docs/MILESTONES.md docs/TASK_BACKLOG.md` — 통과
- `rg "both cards' filenames|preview card filenames" README.md docs/ACCEPTANCE_CRITERIA.md docs/MILESTONES.md docs/TASK_BACKLOG.md` — 0건 (stale wording 잔존 없음)
- `rg "ordered labels" README.md docs/ACCEPTANCE_CRITERIA.md docs/MILESTONES.md docs/TASK_BACKLOG.md` — 4개 문서 모두 올바르게 반영
- `make e2e-test` — 미실행 (docs-only 변경, 테스트 코드 수정 없음)
- `python3 -m unittest -v tests.test_web_app` — 미실행 (server 로직 변경 없음)

---

## 남은 리스크

- smoke 시나리오 수 17 변동 없음
- `docs/PRODUCT_SPEC.md`, `docs/NEXT_STEPS.md`는 generic 수준으로 already truthful하여 이번 라운드에서 변경하지 않았음
- preview-card ordinal-prefix family와 그 docs truth sync가 모두 닫힘. 다음 슬라이스는 새 property family로 이동 가능.
