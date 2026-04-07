# entity-card crimson-desert docs-next-steps exact-field chain-provenance overstatement correction

날짜: 2026-04-07

## 변경 파일
- `docs/NEXT_STEPS.md`

## 사용 skill
- 없음 (docs-only overstatement correction)

## 변경 이유
- `docs/NEXT_STEPS.md:16`의 crimson-desert exact-field clause 끝에 `and full natural-reload follow-up/second-follow-up chain provenance truth-sync`가 붙어 있어, initial exact-field의 `blog.example.com` provenance가 follow-up chain까지 이어지는 것으로 읽힐 여지가 있었습니다.
- actual-search follow-up/second-follow-up truth (`README.md:157/159/165`, `docs/MILESTONES.md:75/77/83`, `docs/ACCEPTANCE_CRITERIA.md:1366/1368/1374`, `docs/TASK_BACKLOG.md:64/66/72`)는 `namu.wiki`, `ko.wikipedia.org` continuity와 drift prevention까지이며, `blog.example.com` provenance는 initial exact-field에만 해당합니다.
- follow-up/second-follow-up chain은 이미 별도의 `entity-card 붉은사막 browser natural-reload follow-up/second-follow-up` clause에서 다루고 있으므로 중복 참조를 제거합니다.

## 핵심 변경
- crimson-desert exact-field clause 끝에서 `, and full natural-reload follow-up/second-follow-up chain provenance truth-sync` 제거
- 기존 initial exact-field wording (`방금 검색한 결과 다시 보여줘` path, `WEB` badge, `설명 카드`, `설명형 다중 출처 합의`, `백과 기반`, negative assertions, provenance) 유지
- scenario count `73` 유지

## 검증
- `git diff --check -- docs/NEXT_STEPS.md`: clean
- README.md, MILESTONES.md, ACCEPTANCE_CRITERIA.md, TASK_BACKLOG.md와의 cross-doc consistency 확인 완료

## 남은 리스크
- 없음 (docs-only correction, 별도 follow-up/second-follow-up clause 및 noisy-single-source family 변경 없음)
