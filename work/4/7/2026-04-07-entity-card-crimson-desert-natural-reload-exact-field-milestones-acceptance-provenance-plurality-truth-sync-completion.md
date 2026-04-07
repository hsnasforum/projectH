# entity-card crimson-desert natural-reload exact-field milestones-acceptance provenance-plurality truth-sync completion

날짜: 2026-04-07

## 변경 파일
- `docs/MILESTONES.md`
- `docs/ACCEPTANCE_CRITERIA.md`

## 사용 skill
- 없음 (docs-only truth-sync correction)

## 변경 이유
- `docs/MILESTONES.md:70`과 `docs/ACCEPTANCE_CRITERIA.md:1361`의 entity-card 붉은사막 natural-reload exact-field line이 context box provenance에 `blog.example.com`만 적고 있어, current truth (`README.md:152`, `docs/TASK_BACKLOG.md:59`, `docs/NEXT_STEPS.md:16`, browser smoke contract)에서 확인되는 `namu.wiki`, `ko.wikipedia.org` source-path plurality가 빠져 있었습니다.

## 핵심 변경
- MILESTONES: context box provenance를 `blog.example.com`만에서 `namu.wiki`, `ko.wikipedia.org`, `blog.example.com`으로 확장
- ACCEPTANCE_CRITERIA: 동일하게 context box provenance 확장
- 기존 `WEB` badge, `설명 카드`, `설명형 다중 출처 합의`, `백과 기반`, negative assertions wording 유지
- scenario count `73` 유지

## 검증
- `git diff --check -- docs/MILESTONES.md docs/ACCEPTANCE_CRITERIA.md`: clean
- README.md:152, TASK_BACKLOG.md:59, NEXT_STEPS.md:16과의 cross-doc consistency 확인 완료

## 남은 리스크
- 없음 (docs-only correction, 다른 family/line 변경 없음)
