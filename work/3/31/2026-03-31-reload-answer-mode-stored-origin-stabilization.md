# 2026-03-31 reload answer_mode stored-origin stabilization

## 변경 파일
- `core/agent_loop.py`
- `tests/test_smoke.py`

## 사용 skill
- 없음

## 변경 이유
- operator가 current-risk reduction 축 → reload answer_mode 추론 불안정(옵션 1)을 선택.
- `_reuse_web_search_record`에서 `summary_text.startswith("웹 최신 확인:")`으로 answer_mode를 추론하여, 요약 텍스트 형태가 바뀌면 `latest_update`가 `general`로 떨어지는 위험이 있었음.
- 저장된 record에는 이미 `response_origin.answer_mode`가 있으므로, 이를 우선 참조하면 추론이 안정적임.

## 핵심 변경

### production 변경 (`core/agent_loop.py`)
1. `_reuse_web_search_record`에서 record의 `response_origin.answer_mode`를 `stored_answer_mode`로 추출
2. answer_mode 추론 로직을 `_infer_reloaded_answer_mode()` 로컬 함수로 통합:
   - `claim_coverage`가 있으면 → `"entity_card"` (기존과 동일)
   - `stored_answer_mode`가 `"entity_card"` 또는 `"latest_update"`이면 → 그대로 사용 (새로 추가)
   - `summary_text.startswith("웹 최신 확인:")`이면 → `"latest_update"` (기존 fallback 유지)
   - 그 외 → `"general"`
3. active_context와 show_only 경로에서 중복되던 answer_mode 추론을 하나로 통합
4. show_only 경로에서 별도로 `reloaded_answer_mode`를 재계산하던 코드 제거 — 통합된 `reloaded_answer_mode` 변수를 사용

### 테스트 변경 (`tests/test_smoke.py`)
- `test_reuse_web_search_record_uses_stored_answer_mode_over_summary_prefix` 추가
  - WebSearchStore에 `answer_mode: "latest_update"` + "웹 최신 확인:" 접두사가 없는 summary_text를 직접 저장
  - reload 경로에서 stored answer_mode가 우선 사용되어 `response_origin["answer_mode"] == "latest_update"` 유지 확인
  - 기존 접두사 기반 추론만으로는 `"general"`로 떨어지는 시나리오를 직접 재현

### 변경하지 않은 것
- UI, docs, approval flow, reviewed-memory, Playwright smoke 변경 없음
- 최초 검색 시 answer_mode 결정 로직 변경 없음 (reload 경로만 변경)
- stored_answer_mode가 빈 문자열이거나 없는 레거시 record에서는 기존 fallback 동작 유지

## 검증
- `python3 -m unittest -v tests.test_smoke`: 90 tests, OK (1.044s)
- `python3 -m unittest -v tests.test_web_app`: 106 tests, OK (1.788s)
- `git diff --check -- core/agent_loop.py tests/test_smoke.py`: 통과

## 남은 리스크
- stored_answer_mode가 없는 레거시 record(response_origin이 빈 dict)에서는 여전히 summary_text 접두사 기반 fallback에 의존함. 현재 모든 검색 결과는 response_origin을 포함하여 저장되므로 실질 위험은 낮음.
- dirty worktree가 여전히 넓음.
