# 2026-04-28 M49 Axis 3 summarization injection web exclusion

## 변경 파일

- `model_adapter/base.py`
- `model_adapter/ollama.py`
- `model_adapter/mock.py`
- `core/agent_loop.py`
- `tests/test_agent_loop.py`
- `tests/test_agent_loop_model_routing.py`
- `tests/test_preference_injection.py`
- `tests/test_smoke.py`
- `tests/test_web_app.py`
- `docs/MILESTONES.md`
- `work/4/28/2026-04-28-m49-axis3-summarization-injection-web-exclusion.md`

## 사용 skill

- `work-log-closeout`: 구현 소유자 라운드 종료 기록의 필수 항목과 실제 검증 결과를 맞추기 위해 사용.

## 변경 이유

`CONTROL_SEQ 1159` handoff가 M49 Axis 1 계약의 남은 두 경계를 함께 닫으라고 지정했다. 문서 요약 `stream_summarize()` 경로에는 선호도가 주입되지 않았고, 웹 조사 context-answer 경로에는 선호도가 들어갈 수 있어 계약과 어긋났다.

## 핵심 변경

- `ModelAdapter.summarize()` / `stream_summarize()` 시그니처에 `active_preferences`를 추가했다.
- `OllamaModelAdapter` 요약 system prompt 앞에 기존 `_format_preference_block()` 결과를 붙이도록 했다. `active_preferences=None`이면 기존 요약 system prompt를 유지한다.
- `MockModelAdapter` 요약/stream 요약 시그니처를 맞추고, 선호도가 있으면 mock prefix에 반영 건수를 표시하게 했다.
- `AgentLoop._summarize_text_with_chunking()` 시작부에서 `_routed_preferences(task="summarize")`를 한 번 계산해 네 `stream_summarize()` 호출에 전달하도록 했다.
- 웹 조사 context-answer 경로는 `_is_web=True`일 때 `active_preferences=None`을 전달하도록 유지해 웹 조사에는 선호도가 주입되지 않게 했다.
- `tests/test_agent_loop.py`, `tests/test_preference_injection.py`, 관련 test double에 summarization 주입과 웹 조사 제외 회귀 테스트/시그니처 정리를 추가했다.
- `docs/MILESTONES.md`의 M49 Axis 3 항목을 `CONTROL_SEQ 1159` 기준 `summarization 주입 + 웹 조사 제외`로 정리했다.

## 검증

- PASS: `sha256sum .pipeline/implement_handoff.md` 결과가 요청된 `3d3b73efa3b345ba4867347c912c8ba1cfc40494785ad21d47dc33c1135bbc3e`와 일치.
- PASS: `python3 -m py_compile model_adapter/base.py model_adapter/ollama.py model_adapter/mock.py core/agent_loop.py tests/test_agent_loop.py tests/test_preference_injection.py tests/test_agent_loop_model_routing.py tests/test_smoke.py tests/test_web_app.py`
- PASS: `python3 -m unittest -v tests.test_agent_loop tests.test_agent_loop_model_routing`
- PASS: `python3 -m unittest -v tests.test_preference_injection`
- PASS: `git diff --check -- model_adapter/base.py model_adapter/ollama.py model_adapter/mock.py core/agent_loop.py docs/MILESTONES.md tests/test_agent_loop.py tests/test_preference_injection.py tests/test_agent_loop_model_routing.py tests/test_smoke.py tests/test_web_app.py`
- PASS: `python3 -m unittest -v tests.test_ollama_adapter`
- PASS(no whitespace diagnostics): `git diff --no-index --check /dev/null work/4/28/2026-04-28-m49-axis3-summarization-injection-web-exclusion.md`

## 남은 리스크

- 전체 브라우저/E2E는 실행하지 않았다. 변경 범위가 model adapter 요약 시그니처, agent loop 요약/context call site, 단위 테스트, milestone 문서에 한정되어 단위 검증으로 제한했다.
- `model_adapter/` 요약 포맷 외 approval flow, storage, preference lifecycle, session/artifact 경계는 변경하지 않았다.
- 작업트리에는 이전 라운드/다른 작업의 untracked report/verify/work 파일이 남아 있으며, 이번 handoff에서는 수정하거나 되돌리지 않았다.
- commit, push, branch/PR publish는 수행하지 않았다.
