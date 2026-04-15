# 검토 후보 review-outcome 잔여 top-doc truth-sync

## 변경 파일

- `README.md`

## 사용 skill

- 없음

## 변경 이유

이전 visibility 라운드가 기능 구현과 focused browser 검증을 완료했으나, `README.md:264`에 "only one reviewed-but-not-applied `accept` action" 서술이 남아 있었습니다. 이 라운드는 해당 잔여 top-doc drift를 한 번에 닫습니다.

## 핵심 변경

1. **`README.md:264`**: "allows only one reviewed-but-not-applied `accept` action that writes source-message `candidate_review_record` without opening user-level memory" → "supports `accept`/`reject`/`defer` reviewed-but-not-applied actions that write source-message `candidate_review_record` and persistently show the review outcome on the source-message transcript meta, without opening user-level memory"

## 검증

- `grep` 대상 5개 docs: `only one reviewed-but-not-applied.*accept`, `accept-only`, `one.*accept.*action is available` → no matches
- `git diff --check` → clean
- pytest / Playwright 재실행 없음 — docs-only 변경

## 남은 리스크

- 대상 top docs에서 review-outcome 관련 accept-only 잔여 서술은 이 라운드로 닫혔습니다.
