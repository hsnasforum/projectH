# 2026-03-31 dual-probe reload active-context retention verification

## 변경 파일
- `verify/3/31/2026-03-31-dual-probe-reload-active-context-retention-verification.md`
- `.pipeline/codex_feedback.md`

## 사용 skill
- `round-handoff`
- `investigation-quality-audit`

## 변경 이유
- 사용자 요청에 따라 `AGENTS.md`, `work/README.md`, `verify/README.md`, `.pipeline/README.md`를 먼저 다시 읽고, latest Claude `/work`인 `work/3/31/2026-03-31-dual-probe-reload-active-context-retention.md`와 latest same-day `/verify`인 `verify/3/31/2026-03-31-dual-probe-active-context-source-path-fix-verification.md`를 기준으로 이번 라운드 주장만 좁게 검수해야 했습니다.
- latest `/work`는 history reload 뒤에도 entity-card dual probe가 `active_context["source_paths"]`에 유지되도록 `_reuse_web_search_record()` 경로를 맞췄다고 적고 있으므로, 이번 검수에서는 해당 reload production 변경, 새 `tests.test_web_app` regression 존재 여부, docs sync 필요성, current MVP 범위 일탈 여부, 그리고 필요한 최소 Python regression만 다시 확인하면 충분했습니다.

## 핵심 변경
- 판정: latest `/work`의 code/test 변경 주장은 현재 코드와 일치합니다.
- `core/agent_loop.py`의 `_reuse_web_search_record()`에는 `entity_sources: list[dict[str, Any]] | None = None` 초기화가 실제로 들어가 있고, entity profile이면 `_select_ranked_web_sources(max_items=3)` 결과를 `entity_sources`에 담은 뒤 `_build_web_search_active_context(... pre_selected_sources=entity_sources, ...)`로 넘기도록 바뀌었습니다.
- `tests/test_web_app.py`에는 `test_handle_chat_entity_card_dual_probe_reload_preserves_active_context_source_paths`가 실제로 추가되어 있고, dual-probe entity-card record를 `WebSearchStore.save()`로 직접 저장한 뒤 `load_web_search_record_id` reload 결과의 `session.active_context.source_paths`에 두 probe URL이 모두 남는지 검증합니다.
- latest `/work`의 `docs 변경 없음` 주장도 이번 라운드에서는 맞습니다. 이번 수정은 entity-card reload evidence/source context 정합성 보정 1건이며, root docs가 exact dual-probe reload retention heuristic까지 current shipped contract로 약속하고 있지는 않습니다.
- 범위 역시 현재 projectH 방향에서 벗어나지 않습니다. web investigation remains secondary, read-only, permission-gated, and logged라는 경계 안에서 entity-card history reload의 source-context 정합성만 좁게 보정했고, approval flow, reviewed-memory, UI, Playwright, latest_update/live family, 문서 계약 확장은 확인되지 않았습니다.
- 다만 현재 regression은 dual-probe record를 직접 저장한 뒤 reload합니다. 따라서 same-family 남은 smallest shipped-flow risk는 “실제 entity search가 저장한 record”를 history-card reload했을 때도 같은 `active_context["source_paths"]` retention이 유지되는지 end-to-end에 더 가까운 regression으로 잠그는 일입니다. 이건 다음 슬라이스 선정 근거이며, 이번 round의 truth 판정 자체를 바꾸지는 않습니다.
- whole-project audit이 필요한 징후는 아니므로 `report/`는 만들지 않았습니다.

## 검증
- `python3 -m unittest -v tests.test_web_app`
  - 통과 (`Ran 111 tests`, `OK`)
- `git diff --check -- core/agent_loop.py tests/test_web_app.py`
  - 통과 (출력 없음)
- 수동 truth 대조
  - `work/3/31/2026-03-31-dual-probe-reload-active-context-retention.md`
  - `verify/3/31/2026-03-31-dual-probe-active-context-source-path-fix-verification.md`
  - `.pipeline/codex_feedback.md`
  - `docs/TASK_BACKLOG.md`
  - `docs/MILESTONES.md`
  - `docs/NEXT_STEPS.md`
  - `core/agent_loop.py`
  - `tests/test_web_app.py`
- 추가 확인
  - `git diff -- core/agent_loop.py tests/test_web_app.py tests/test_smoke.py`
  - `rg -n "pre_selected_sources|_reuse_web_search_record|load_web_search_record_id|boardNo=200|boardNo=300|active_context\\[\\\"source_paths\\\"\\]" core/agent_loop.py tests/test_web_app.py tests/test_smoke.py`
  - `sed -n '5831,5950p' core/agent_loop.py`
  - `sed -n '8388,8438p' tests/test_web_app.py`
  - `stat -c '%y %n' core/agent_loop.py tests/test_web_app.py work/3/31/2026-03-31-dual-probe-reload-active-context-retention.md verify/3/31/2026-03-31-dual-probe-active-context-source-path-fix-verification.md .pipeline/codex_feedback.md`
- 이번 라운드에서 재실행하지 않은 검증
  - `python3 -m unittest -v tests.test_smoke`
  - `make e2e-test`
  - 이유: 이번 변경은 `_reuse_web_search_record()` reload 경로와 `tests.test_web_app` service regression 1건을 중심으로 한 backend investigation slice였고, browser-visible markup/CSS나 docs wording 자체는 바뀌지 않았으므로 `tests.test_web_app`과 scoped diff check만으로 직접 영향 범위를 재검수할 수 있었습니다.

## 남은 리스크
- 현재 새 regression은 dual-probe record를 `WebSearchStore.save()`로 직접 저장한 뒤 reload하는 좁은 path만 고정합니다. 실제 entity search가 만든 record를 history-card reload했을 때도 같은 `active_context["source_paths"]` retention이 유지되는지는 아직 explicit regression으로 잠겨 있지 않습니다.
- 최신 변경 덕분에 `_reuse_web_search_record()` 내부 구조는 `record_id` 유무와 무관하게 공통이지만, 실제 initial search → stored record → history-card reload shipped flow 전체를 한 번에 잠그는 테스트는 여전히 별도 가치가 있습니다.
- dirty worktree가 여전히 넓어 다음 검수도 unrelated 변경을 끌어오지 않도록 scoped verification discipline이 계속 필요합니다.
