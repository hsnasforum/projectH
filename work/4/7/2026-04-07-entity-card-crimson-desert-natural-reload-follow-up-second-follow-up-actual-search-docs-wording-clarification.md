# entity-card crimson-desert natural-reload follow-up/second-follow-up actual-search docs wording clarification

날짜: 2026-04-07

## 변경 파일
- `README.md`
- `docs/NEXT_STEPS.md`
- `docs/MILESTONES.md`
- `docs/ACCEPTANCE_CRITERIA.md`
- `docs/TASK_BACKLOG.md`

## 사용 skill
- 없음 (docs-only wording clarification)

## 변경 이유
- crimson natural-reload follow-up/second-follow-up continuity lines가 `actual-search` qualifier 없이 적혀 있어, 바로 아래 noisy-exclusion lines와 같은 붉은사막 family 문맥에서 branch 구분이 약했습니다.
- dedicated test anchors는 `entity-actual-search-natural-reload-followup-sp`, `test_handle_chat_actual_entity_search_natural_reload_follow_up_preserves_source_paths` 등으로 actual-search branch를 직접 명시합니다.

## 핵심 변경
- 5개 파일의 follow-up + second-follow-up continuity lines에 `actual-search` qualifier 추가
- README.md: line 159, 165
- MILESTONES.md: line 77, 85
- ACCEPTANCE_CRITERIA.md: line 1368, 1376
- TASK_BACKLOG.md: line 66, 74
- NEXT_STEPS.md: line 16 general continuity clause
- two-source truth (`namu.wiki`, `ko.wikipedia.org`), noisy-exclusion wording 변경 없음
- scenario count 75 유지

## 검증
- `git diff --check`: clean
- cross-doc consistency 확인 완료

## 남은 리스크
- 없음 (docs-only wording clarification)
