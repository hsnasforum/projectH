# 2026-03-31 multi-source count-based metadata smoke assertion

## 목표
browser folder picker 다중 출처 검색 응답에서 quick-meta와 transcript meta가 `출처 2개` count-based metadata를 유지하고, 단일 basename으로 무너지지 않는다는 현재 shipped 계약을 browser smoke로 고정.

## 변경 파일
- `e2e/tests/web-smoke.spec.mjs`:
  - `memo.md` fixture에 "budget reference" 추가하여 "budget" 검색 시 2개 파일 모두 매칭되도록 조정
  - folder-search scenario(scenario 3)에 quick-meta/transcript meta `출처 2개` positive assertion 추가
  - quick-meta/transcript meta에 단일 basename(`budget-plan.md`, `memo.md`)이 `출처` 뒤에 직접 노출되지 않는 negative assertion 추가
- `README.md`: scenario 3 설명에 multi-source count-based metadata coverage 반영
- `docs/ACCEPTANCE_CRITERIA.md`: scenario 3 설명에 multi-source count-based metadata coverage 반영
- `docs/MILESTONES.md`: smoke suite 설명에 multi-source count-based metadata coverage 반영
- `docs/TASK_BACKLOG.md`: smoke coverage 설명에 multi-source count-based metadata coverage 반영

## 변경 내용
- `memo.md` fixture에 "budget reference" 한 줄 추가 → "budget" 검색 시 `_search_uploaded_files`가 content match로 memo.md도 잡아서 `selected_source_paths`가 2개가 됨.
- folder-search scenario에서:
  - `#response-quick-meta-text`가 `출처 2개`를 포함하는지 positive assert
  - `#response-quick-meta-text`가 `출처 budget-plan.md` / `출처 memo.md` 형태가 아닌지 regex negative assert
  - transcript meta `.last()`에 동일한 positive/negative assert
- 기존 `#selected-text`의 `budget-plan.md` positive assert는 그대로 유지 (response body/selected 영역은 범위 밖).

## 검증
- `git diff --check`: whitespace 오류 없음
- `make e2e-test`: 13 passed (전체 통과)

## 리스크
- `memo.md` fixture content 변경이 다른 scenario에 영향을 줄 수 있으나, 현재 memo.md를 직접 사용하는 scenario는 folder-search 하나뿐이므로 영향 없음.
- negative assertion은 regex(`/출처\s+budget-plan\.md/`)로 한정하여, response body나 selected-text에 basename이 나오는 정상 동작은 차단하지 않음.

## 사용 스킬
- 없음 (직접 편집)
