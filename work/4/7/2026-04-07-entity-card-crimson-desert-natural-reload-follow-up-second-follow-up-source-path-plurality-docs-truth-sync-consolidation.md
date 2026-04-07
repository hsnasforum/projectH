# entity-card crimson-desert natural-reload follow-up/second-follow-up source-path plurality docs truth-sync consolidation

날짜: 2026-04-07

## 변경 파일
- `README.md`
- `docs/MILESTONES.md`
- `docs/ACCEPTANCE_CRITERIA.md`
- `docs/TASK_BACKLOG.md`

## 사용 skill
- 없음 (docs-only consolidation)

## 변경 이유
- crimson natural-reload follow-up/second-follow-up general continuity docs가 `namu.wiki`, `ko.wikipedia.org`만 적고 있어, dedicated noisy-exclusion docs/browser anchors가 이미 적고 있는 `blog.example.com` provenance continuity와 같은 flow에서 두 단계로 갈라져 보였습니다.
- shipped truth (service tests: `tests/test_web_app.py:17327/17386`, browser: `e2e/tests/web-smoke.spec.mjs:5178/5260`)는 `blog.example.com` provenance를 context box에서 함께 확인합니다.

## 핵심 변경
- README.md: follow-up (line 159) + second-follow-up (line 165) source path에 `blog.example.com` provenance 추가
- MILESTONES.md: follow-up (line 77) + second-follow-up (line 85) source-path plurality에 `blog.example.com` provenance 추가
- ACCEPTANCE_CRITERIA.md: follow-up (line 1368) + second-follow-up (line 1376) source path에 `blog.example.com` provenance 추가
- TASK_BACKLOG.md: follow-up (line 66) + second-follow-up (line 74) source-path plurality에 `blog.example.com` provenance 추가
- scenario count 75 유지

## 검증
- `git diff --check`: clean
- cross-doc consistency: dedicated noisy-exclusion lines와 general continuity lines가 동일 provenance plurality 수준으로 정렬 확인

## 남은 리스크
- 없음 (docs-only consolidation, runtime/test 변경 없음)
