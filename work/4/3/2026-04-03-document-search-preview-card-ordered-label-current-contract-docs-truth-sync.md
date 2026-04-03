# 2026-04-03 document-search preview-card ordered-label current-contract docs truth sync

**범위**: current-contract 문서 3개의 preview card wording을 shipped ordered-label truth에 맞게 동기화

---

## 변경 파일

- `README.md` — `matched file's name` → `matched file's ordered label`
- `docs/PRODUCT_SPEC.md` — `matched file's name` → `matched file's ordered label`
- `docs/ACCEPTANCE_CRITERIA.md` — `matched file's name` → `matched file's ordered label`

---

## 사용 skill

- `work-log-closeout`

---

## 변경 이유

`app/static/app.js`는 preview card 이름을 `(idx + 1) + ". " + fileName`으로 렌더링하고, `e2e/tests/web-smoke.spec.mjs`는 search-plus-summary와 search-only 양쪽에서 `1. budget-plan.md`, `2. memo.md` ordered-label direct assertion을 포함합니다. 이전 라운드에서 smoke coverage 요약 문서 4개(`README.md` smoke section, `docs/MILESTONES.md`, `docs/TASK_BACKLOG.md`)는 이미 ordered-label wording으로 맞춰졌지만, current-contract 서술인 `README.md` Current Product Slice, `docs/PRODUCT_SPEC.md`, `docs/ACCEPTANCE_CRITERIA.md`는 여전히 generic `matched file's name`으로 과소서술하고 있었습니다.

---

## 핵심 변경

1. 3개 current-contract 문서에서 `matched file's name` → `matched file's ordered label` (각 1곳씩)
2. full path tooltip / match badge / snippet contract은 변경 없음
3. code/test 파일, runtime behavior 변경 없음

---

## 검증

- `git diff --check -- README.md docs/PRODUCT_SPEC.md docs/ACCEPTANCE_CRITERIA.md` — 통과
- `rg "matched file's name" README.md docs/PRODUCT_SPEC.md docs/ACCEPTANCE_CRITERIA.md` — 0건 (stale wording 잔존 없음)
- `rg "ordered label" README.md docs/PRODUCT_SPEC.md docs/ACCEPTANCE_CRITERIA.md` — 3개 문서 모두 올바르게 반영
- `rg "1\\. budget-plan\\.md|2\\. memo\\.md|idx \\+ 1|search-preview-name" e2e/tests/web-smoke.spec.mjs app/static/app.js` — smoke truth 확인
- `make e2e-test` — 미실행 (docs-only 변경, code/test 수정 없음)
- `python3 -m unittest -v tests.test_web_app` — 미실행 (server 로직 변경 없음)

---

## 남은 리스크

- preview-card ordered-label family의 current-contract docs truth sync가 모두 닫힘
- smoke 시나리오 수 17 변동 없음
- 다음 슬라이스는 새 property family로 이동 가능
