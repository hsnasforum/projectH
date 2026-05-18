# 2026-04-30 M116 Axis 1 선호 주입 관련성 품질 개선

## 변경 파일

- `core/agent_loop.py`
- `tests/test_agent_loop.py`
- `work/4/30/2026-04-30-m116-axis1-preference-injection-quality.md`

## 사용 skill

- `security-gate`: `preference_injected` 감사 로그가 기존 로컬 task log 경계 안에 남고, 로그 실패가 응답 주입을 막지 않는지 점검.
- `finalize-lite`: 구현 종료 전 검증 범위와 문서 동기화 제외 사유, `/work` closeout 필요 여부를 점검.
- `work-log-closeout`: closeout 형식과 필수 섹션을 맞추기 위해 사용.

## 변경 이유

- M115의 단순 공백 분리 키워드 중첩은 `the`, `is`, `should` 같은 일반 단어로 관련 없는 ACTIVE 선호가 선택될 수 있었다.
- M116 Axis 1 handoff는 최소 stop-word 제거, overlap 점수 정렬, 동점 시 `is_highly_reliable == True` 선호 우선순위를 코드와 단위 테스트로 고정하는 범위다.

## 핵심 변경

- `_get_active_preferences()`가 사용자 입력 텀을 먼저 계산한 뒤 `_select_context_relevant_preferences()`에 전달하도록 리팩터했다.
- `_preference_context_terms()`에 handoff가 지정한 최소 stop-word 집합을 적용해 2자 이상 유효 텀만 반환하도록 했다.
- `_select_context_relevant_preferences()`가 overlap 점수 내림차순으로 관련 선호를 정렬하고, 점수가 같으면 `is_highly_reliable == True` 선호를 먼저 반환하도록 했다.
- stop-word 단독 입력은 관련 선호로 보지 않고 기존 `fallback_all` 동작을 유지한다.
- `tests/test_agent_loop.py`에 stop-word 제거, stop-word-only fallback, overlap 점수 정렬, 동점 시 high-reliable 우선 테스트를 추가했다.
- `is_highly_reliable_preference()`와 `activate_preference()`는 수정하지 않았다.

## 검증

- `python3 -m py_compile core/agent_loop.py`
  - 통과.
- `python3 -m unittest -v tests.test_agent_loop`
  - 통과. 14개 테스트 실행.
- `python3 -m unittest -v tests.test_agent_loop_model_routing`
  - 통과. 5개 테스트 실행.
- `git diff --check -- core/agent_loop.py tests/test_agent_loop.py`
  - 통과.

## 남은 리스크

- 이번 라운드는 Axis 1 코드/테스트 범위라 product docs, UI/frontend, Playwright E2E는 수정하거나 실행하지 않았다.
- stop-word 목록은 handoff가 지정한 최소 집합으로 고정했으므로, 목록 밖의 일반 단어에 의한 과잉 매칭 가능성은 남아 있다.
