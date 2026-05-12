# 2026-04-28 M49 Axis 3 web investigation preference exclusion

## 변경 파일

- `core/agent_loop.py`
- `tests/test_agent_loop.py`
- `docs/MILESTONES.md`
- `work/4/28/2026-04-28-m49-axis3-web-investigation-preference-exclusion.md`

## 사용 skill

- `work-log-closeout`: 구현 소유자 라운드 종료 기록의 필수 항목과 실제 검증 결과를 맞추기 위해 사용.

## 변경 이유

`CONTROL_SEQ 1158` handoff가 M49 Axis 1 계약의 "웹 조사 미적용" 경계를 구현으로 고정하라고 지정했다. 기존 `_respond_with_active_context()`는 `active_context.kind == "web_search"`일 때도 `_routed_preferences()`를 호출해 `stream_answer_with_context()`에 선호도를 전달할 수 있었다.

## 핵심 변경

- `core/agent_loop.py`의 context answer call site에서 `_is_web=True`이면 `active_preferences=None`을 전달하도록 조건을 추가했다.
- 일반 chat 경로의 `stream_respond(... active_preferences=_prefs)` 호출은 변경하지 않았다.
- `_routed_preferences()` 내부는 변경하지 않고, handoff 지시대로 call site 조건만 추가했다.
- `tests/test_agent_loop.py`에 웹 조사 active context 응답 경로가 `_routed_preferences()`를 호출하지 않고 모델에 `active_preferences=None`을 전달하는 단위 테스트를 추가했다.
- `docs/MILESTONES.md`의 M49 항목에 Axis 3 ACTIVE 문구를 추가했다.

## 검증

- PASS: `sha256sum .pipeline/implement_handoff.md` 결과가 요청된 `559a8d8883037ee7f40a54d7aa5d5920d652c271ea95f90beca6056bddec0376`와 일치.
- PASS: `python3 -m py_compile core/agent_loop.py tests/test_agent_loop.py`
- PASS: `python3 -m unittest -v tests.test_agent_loop`
- PASS: `git diff --check -- core/agent_loop.py docs/MILESTONES.md`
- PASS(no whitespace diagnostics): `git diff --no-index --check /dev/null tests/test_agent_loop.py`
- PASS(no whitespace diagnostics): `git diff --no-index --check /dev/null work/4/28/2026-04-28-m49-axis3-web-investigation-preference-exclusion.md`
- PASS: `python3 -m unittest -v tests.test_agent_loop_model_routing`
- PASS: `grep -n "M49\|Axis 3\|웹 조사 경로\|stream_answer_with_context" docs/MILESTONES.md`

## 남은 리스크

- 이번 라운드는 웹 조사 context answer 경로의 선호도 제외만 수행했다. `model_adapter/`, approval flow, storage, preference lifecycle은 변경하지 않았다.
- 전체 브라우저/E2E는 실행하지 않았다. 변경 범위가 agent loop call site, 단위 테스트, milestone 문서에 한정되어 단위 검증으로 제한했다.
- 작업트리에는 이전 라운드/다른 작업의 dirty 파일과 untracked `/work` 파일이 남아 있으며, 이번 handoff에서는 수정하거나 되돌리지 않았다.
- commit, push, branch/PR publish는 수행하지 않았다.
