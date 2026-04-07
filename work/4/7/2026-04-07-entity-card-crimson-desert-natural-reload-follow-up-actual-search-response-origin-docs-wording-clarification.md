# entity-card crimson-desert natural-reload follow-up actual-search response-origin docs wording clarification

날짜: 2026-04-07

## 변경 파일
- `README.md`
- `docs/MILESTONES.md`
- `docs/ACCEPTANCE_CRITERIA.md`
- `docs/TASK_BACKLOG.md`

## 사용 skill
- 없음 (docs-only wording clarification)

## 변경 이유
- crimson natural-reload follow-up response-origin continuity line 4곳이 `actual-search` qualifier 없이 적혀 있어, 이미 qualifier가 붙은 source-path line 및 noisy-exclusion line과 branch 구분이 약했습니다.
- dedicated anchors (`e2e/tests/web-smoke.spec.mjs:4990`, `tests/test_web_app.py:16511`)는 actual entity-search follow-up response-origin을 직접 명시합니다.

## 핵심 변경
- README.md:157, MILESTONES.md:75, ACCEPTANCE_CRITERIA.md:1366, TASK_BACKLOG.md:64의 follow-up response-origin line에 `actual-search` qualifier 추가
- response-origin wording (WEB, 설명 카드, 설명형 다중 출처 합의, 백과 기반) 변경 없음
- scenario count 75 유지

## 검증
- `git diff --check`: clean
- cross-doc consistency 확인 완료

## 남은 리스크
- 없음 (follow-up response-origin + source-path 모두 actual-search qualifier 완료, second-follow-up도 이전 라운드에서 완료)
