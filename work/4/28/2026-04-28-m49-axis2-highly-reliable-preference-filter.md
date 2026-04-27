# 2026-04-28 M49 Axis 2 highly reliable preference filter

## 변경 파일

- `core/agent_loop.py`
- `app/handlers/preferences.py`
- `storage/preference_utils.py`
- `tests/test_agent_loop.py`
- `docs/MILESTONES.md`
- `work/4/28/2026-04-28-m49-axis2-highly-reliable-preference-filter.md`

## 사용 skill

- `work-log-closeout`: 구현 소유자 라운드 종료 기록의 필수 항목과 실제 검증 결과를 맞추기 위해 사용.

## 변경 이유

`CONTROL_SEQ 1154` handoff가 M49 Axis 2로 `_get_active_preferences()`의 기본 반환 대상을 ACTIVE 전체에서 `is_highly_reliable=True` 선호도로 좁히라고 지정했다. M49 Axis 1에서 확정한 계약대로, 선호도 주입은 기본적으로 신뢰도 높은 선호만 읽기 전용으로 모델 호출에 전달해야 했다.

## 핵심 변경

- `storage/preference_utils.py`를 추가해 preference fingerprint 정규화, `quality_info`, `reliability_stats`, `is_highly_reliable` 계산을 공유 helper로 분리했다.
- `app/handlers/preferences.py`의 기존 `_is_highly_reliable_preference()`는 새 공유 helper에 위임하고, `list_preferences_payload()`도 같은 enrichment helper를 사용하게 했다.
- `core/agent_loop.py`의 `_get_active_preferences()`에 `highly_reliable_only=True` 기본 인자를 추가하고, 기본 경로에서 highly reliable 선호만 반환하도록 했다.
- agent loop는 `session_store.get_global_audit_summary().per_preference_stats`와 preference의 `avg_similarity_score` 또는 기존 `quality_info`를 사용해 handler와 같은 신뢰도 기준을 적용한다.
- `tests/test_agent_loop.py`를 추가해 store 없음, 기본 low-quality 제외, 기본 low-application 제외, `highly_reliable_only=False` 전체 active 반환을 고정했다.
- `docs/MILESTONES.md`의 M49 항목에 Axis 2 ACTIVE 문구를 추가했다.

## 검증

- PASS: `sha256sum .pipeline/implement_handoff.md` 결과가 요청된 `59d37e85c1607a4fdcf5dddd7bff0172f6bed86808db85ffbc2c0ba54457f498`와 일치.
- PASS: `python3 -m py_compile core/agent_loop.py app/handlers/preferences.py storage/preference_utils.py tests/test_agent_loop.py`
- PASS: `python3 -m unittest -v tests.test_agent_loop`
- PASS: `python3 -m unittest -v tests.test_agent_loop tests.test_agent_loop_model_routing tests.test_preference_handler`
- PASS: `git diff --check -- core/agent_loop.py app/handlers/preferences.py docs/MILESTONES.md`
- PASS(no whitespace diagnostics): `git diff --no-index --check /dev/null storage/preference_utils.py`
- PASS(no whitespace diagnostics): `git diff --no-index --check /dev/null tests/test_agent_loop.py`
- PASS: `grep -n "M49\|is_highly_reliable 필터\|_get_active_preferences" docs/MILESTONES.md`

## 남은 리스크

- 이번 라운드는 선호도 주입 후보 필터만 바꿨다. `model_adapter/` 주입 포맷, approval flow, preference lifecycle, web investigation 경로는 변경하지 않았다.
- 전체 브라우저/E2E는 실행하지 않았다. 변경 범위가 agent loop preference filtering, handler helper 공유, 단위 테스트, milestone 문서에 한정되어 단위 검증으로 제한했다.
- 기존 작업트리에는 이번 라운드 이전의 `docs/TASK_BACKLOG.md` 수정과 pipeline runtime 관련 dirty 파일이 남아 있으며, 이번 handoff에서는 수정하거나 되돌리지 않았다.
- commit, push, branch/PR publish는 수행하지 않았다.
