# 검토 후보 action vocabulary 남은 root-doc parity bundle

## 변경 파일

- `docs/ACCEPTANCE_CRITERIA.md`
- `docs/TASK_BACKLOG.md`

## 사용 skill

- 없음

## 변경 이유

이전 두 차례 docs cleanup bundle이 `docs/NEXT_STEPS.md`와 `docs/PRODUCT_SPEC.md`의 주요 accept-only 서술을 수정했으나, `docs/ACCEPTANCE_CRITERIA.md:365`와 `docs/TASK_BACKLOG.md:192`에 current-slice accept-only 서술이 남아 있었습니다. 이 라운드는 남은 root-doc family를 한 번에 닫습니다.

## 핵심 변경

1. **`docs/ACCEPTANCE_CRITERIA.md:365`**: "one `accept` action is available in the current slice / that action records reviewed-but-not-applied state only" → "`accept`, `reject`, and `defer` actions are available / all three actions record reviewed-but-not-applied state only"
2. **`docs/TASK_BACKLOG.md:192`**: "one `accept` action can record source-message `candidate_review_record`" → "`accept`/`reject`/`defer` actions can record source-message `candidate_review_record`"

## 검증

- `grep -ri` 대상 5개 docs: `accept.only`, `accept-only`, `no reject`, `no defer`, `review_action = accept`, `review_status = accepted`, `one.*accept.*action`, `only.*accept.*is implemented` 등 → no matches
- `git diff --check` → clean
- pytest / Playwright 재실행 없음 — docs-only 변경

## 남은 리스크

- 대상 5개 root docs에서 accept-only current-slice 서술은 이 라운드로 완전히 닫혔습니다.
