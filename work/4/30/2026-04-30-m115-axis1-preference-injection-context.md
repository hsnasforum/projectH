# 2026-04-30 M115 Axis 1 선호 주입 컨텍스트 관련성

## 변경 파일

- `core/agent_loop.py`
- `tests/test_agent_loop.py`
- `work/4/30/2026-04-30-m115-axis1-preference-injection-context.md`

## 사용 skill

- `security-gate`: `preference_injected` task log 이벤트 추가가 로컬 감사 로그 경계를 넘지 않는지 점검.
- `finalize-lite`: 구현 종료 전 검증 범위, 문서 동기화 범위, `/work` closeout 필요 여부를 점검.
- `work-log-closeout`: closeout 형식과 필수 섹션을 맞추기 위해 사용.

## 변경 이유

- M114 이후 사용자 수동 활성화 선호가 즉시 주입될 수 있게 되면서, 현재 사용자 입력과 무관한 ACTIVE 선호까지 무조건 주입될 가능성이 생겼다.
- M115 Axis 1은 복잡한 NLP 없이 단순 키워드 중첩 기준으로 주입 후보를 좁히고, 실제 주입된 선호를 task log에 남기는 범위다.

## 핵심 변경

- `AgentLoop._get_active_preferences()`가 `user_input`과 `session_id`를 선택적으로 받아, 기존 `is_highly_reliable_preference()` 선행 필터 이후 컨텍스트 관련성 필터를 적용한다.
- `description` 또는 `corrected_text` 단어 집합과 `user_input` 단어 집합이 1개 이상 겹치는 선호만 우선 선택한다.
- `user_input`이 없거나 관련 선호가 0개이면 기존처럼 전체 후보를 반환하는 `fallback_all` 동작을 유지한다.
- `_routed_preferences()`와 summary / active-context answer / general response 경로에서 현재 `request.user_text`와 `session_id`를 전달한다.
- 선택된 선호마다 `preference_injected` task log 이벤트를 남기며, detail에는 `preference_id`, `reason`, `user_input_snippet`을 기록한다.
- task log 기록 실패는 선호 주입을 막지 않도록 개별 이벤트 단위로 예외를 무시한다.
- `tests/test_agent_loop.py`에 no-user-input, context-match, no-match fallback, `preference_injected` 기록 테스트를 추가했다.

## 검증

- `python3 -m py_compile core/agent_loop.py`
  - 통과.
- `python3 -m unittest -v tests.test_agent_loop`
  - 통과. 10개 테스트 실행.
- `python3 -m unittest -v tests.test_agent_loop_model_routing`
  - 통과. 5개 테스트 실행.
- `git diff --check -- core/agent_loop.py`
  - 통과.
- `git diff --check -- core/agent_loop.py tests/test_agent_loop.py`
  - 통과.

## 남은 리스크

- 단순 공백 분리 키워드 중첩이라 `should` 같은 일반 단어도 관련성으로 잡힐 수 있다. 핸드오프가 복잡한 NLP/벡터 검색을 금지했으므로 stop-word 제거는 추가하지 않았다.
- `preference_injected` 이벤트의 product docs 반영은 이번 Axis 1 handoff 범위 밖이라 수행하지 않았다.
- UI/frontend/E2E는 핸드오프 금지 범위라 수정하거나 실행하지 않았다.
