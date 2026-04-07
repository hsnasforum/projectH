# entity-card crimson-desert docs-next-steps follow-up-second-follow-up provenance-overstatement correction

날짜: 2026-04-07

## 변경 파일
- `docs/NEXT_STEPS.md`

## 사용 skill
- 없음 (docs-only overstatement correction)

## 변경 이유
- `docs/NEXT_STEPS.md:16`의 `entity-card 붉은사막 browser natural-reload follow-up/second-follow-up` clause가 `blog.example.com` provenance를 포함하고 있었으나, 이는 noisy-single-source claim family에만 해당하는 truth입니다.
- actual-search crimson-desert follow-up/second-follow-up의 current truth (`README.md:157/159/165`, `docs/MILESTONES.md:75/77/83`, `docs/ACCEPTANCE_CRITERIA.md:1366/1368/1374`, `docs/TASK_BACKLOG.md:64/66/72`, browser smoke/service assertions)는 `WEB`, `설명 카드`, `설명형 다중 출처 합의`, `백과 기반`, `namu.wiki`, `ko.wikipedia.org` continuity까지이며 `blog.example.com` provenance는 포함하지 않습니다.

## 핵심 변경
- crimson-desert follow-up/second-follow-up clause에서 `and `blog.example.com` provenance` 제거
- 기존 `WEB` badge, `설명 카드`, `설명형 다중 출처 합의`, `백과 기반`, `namu.wiki`, `ko.wikipedia.org` drift prevention wording 유지
- noisy-single-source claim family summary의 `blog.example.com` provenance는 그대로 유지 (이번 범위 밖)
- scenario count `73` 유지

## 검증
- `git diff --check -- docs/NEXT_STEPS.md`: clean
- README.md, MILESTONES.md, ACCEPTANCE_CRITERIA.md, TASK_BACKLOG.md와의 cross-doc consistency 확인 완료

## 남은 리스크
- 없음 (docs-only correction, noisy-single-source family summary 및 다른 family wording 변경 없음)
