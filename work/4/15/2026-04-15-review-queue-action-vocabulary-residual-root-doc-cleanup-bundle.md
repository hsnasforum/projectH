# 검토 후보 action vocabulary 잔여 root-doc cleanup bundle

## 변경 파일

- `docs/NEXT_STEPS.md`
- `docs/PRODUCT_SPEC.md`

## 사용 skill

- 없음

## 변경 이유

이전 docs truth-sync bundle이 주요 drift를 줄였으나, `docs/NEXT_STEPS.md`와 `docs/PRODUCT_SPEC.md` 깊은 곳에 accept-only 서술이 4곳 남아 있었습니다. 이 라운드는 잔여 drift를 한 번에 닫는 bounded cleanup입니다.

## 핵심 변경

1. **`docs/NEXT_STEPS.md:530`**: "only `accept` is implemented" → "`accept`, `reject`, and `defer` are all implemented"
2. **`docs/NEXT_STEPS.md:541`**: "the repo still has no `edit` / `reject` / `defer` API" → "the repo still has no `edit` API" (reject/defer는 이미 shipped)
3. **`docs/NEXT_STEPS.md:546`**: "later `edit` / `reject` / `defer` review actions after the shipped first `accept` slice" → "later `edit` review action beyond the shipped `accept` / `reject` / `defer` slice"
4. **`docs/PRODUCT_SPEC.md:1476`**: "the current first `accept` review action" → "the current shipped review actions (`accept`/`reject`/`defer`)"

## 검증

- `grep -ri "accept.only\|accept-only\|no reject\|no defer\|review_action = accept\|review_status = accepted"` 대상 5개 docs → no matches
- 추가 패턴 grep (`only.*accept.*is implemented` 등) → no matches
- `git diff --check` → clean
- pytest / Playwright 재실행 없음 — docs-only 변경이며 코드 무변경

## 남은 리스크

- 잔여 accept-only root-doc drift는 이 라운드로 닫혔습니다. historical `/work`, `/verify` 메모는 당시 시점 기록이므로 수정하지 않았습니다.
