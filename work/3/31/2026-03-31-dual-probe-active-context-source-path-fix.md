# 2026-03-31 dual-probe active-context source-path fix

## 변경 파일
- `core/agent_loop.py`
- `tests/test_smoke.py`

## 사용 skill
- 없음

## 변경 이유
- `.pipeline/codex_feedback.md`가 `STATUS: implement`로, dual probe 공존이 `active_context["source_paths"]`에서도 유지되는지 확인하도록 지시.
- 이전 라운드에서 `selected_source_paths`(전체 serialized_results에서 추출)에는 두 probe가 있었지만, `active_context["source_paths"]`(별도 `_select_ranked_web_sources(max_items=5)` 호출)에는 하나만 있었음.
- 근본 원인: `_build_web_search_active_context`가 독립적으로 source selection을 다시 수행하여, entity claims selection 결과와 불일치.

## 핵심 변경

### production 변경 (`core/agent_loop.py`)
1. `_build_web_search_active_context`에 `pre_selected_sources` optional parameter 추가
   - 전달 시 내부 `_select_ranked_web_sources` 호출을 건너뛰고 전달된 sources를 직접 사용
   - 미전달 시 기존 동작 유지 (하위 호환)
2. entity-card 경로에서 `_build_web_search_active_context` 호출 시 `pre_selected_sources=entity_sources` 전달
   - entity claims selection과 active_context source_paths가 동일한 selection 결과를 공유
3. `entity_sources` 변수를 entity claims 블록 이전에 `None`으로 초기화하여 non-entity 경로에서도 안전하게 전달 가능

### 테스트 변경 (`tests/test_smoke.py`)
- `test_web_search_entity_dual_probe_different_slots_coexist_on_same_domain` assertion을 `active_context["source_paths"]`로 변경
  - 이전: `selected_source_paths`만 검증 (전체 results URL 목록)
  - 변경: `active_context["source_paths"]`를 검증 (user-visible evidence/source context에 실제 노출되는 source 목록)
- fixture의 서비스 probe 텍스트를 "운영하는 게임"으로 수정하여 fact extraction이 "서비스/배급" 슬롯에 정확히 매칭되도록 조정

### 변경하지 않은 것
- UI, docs, approval flow, reviewed-memory, Playwright smoke 변경 없음
- non-entity 경로(latest_update, general)의 `_build_web_search_active_context` 동작 유지
- reload(`_reuse_web_search_record`) 경로의 `_build_web_search_active_context` 동작 유지

## 검증
- `python3 -m unittest -v tests.test_smoke`: 93 tests, OK (1.059s)
- `python3 -m unittest -v tests.test_web_app`: 110 tests, OK (1.800s)
- `git diff --check -- core/agent_loop.py tests/test_smoke.py`: 통과

## 남은 리스크
- non-entity 경로에서는 `pre_selected_sources`가 None이므로 기존 독립 selection이 유지됨. entity-card 이외 경로에서 source_paths 불일치가 발생할 가능성은 현재 없지만, 향후 다른 answer_mode에서도 pre-selection이 필요하면 동일 패턴 적용 필요.
- dirty worktree가 여전히 넓음.
