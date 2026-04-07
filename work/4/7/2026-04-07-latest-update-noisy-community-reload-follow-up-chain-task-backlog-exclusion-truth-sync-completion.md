# latest-update noisy-community reload follow-up-chain task-backlog exclusion truth-sync completion

## 변경 파일
- `docs/TASK_BACKLOG.md`

## 사용 skill
- 없음 (handoff 기반 직접 구현)

## 변경 이유
- TASK_BACKLOG의 noisy-community follow-up chain 4개 항목(72-75번)이 exclusion surface scope와 positive retention URL을 빠뜨려 root docs보다 약했습니다.

## 핵심 변경
- 4개 항목 모두 `origin detail, response body, context box` exclusion surface 명시
- 4개 항목 모두 `hankyung.com`, `mk.co.kr` positive retention 추가

## 검증
- `git diff --check`: clean

## 남은 리스크
- scenario count 73 유지.
