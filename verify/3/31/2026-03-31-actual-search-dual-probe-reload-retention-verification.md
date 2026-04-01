# 2026-03-31 actual-search dual-probe reload active-context retention verification

## 변경 파일
- `verify/3/31/2026-03-31-actual-search-dual-probe-reload-retention-verification.md`
- `.pipeline/codex_feedback.md`

## 사용 skill
- `round-handoff`
- `investigation-quality-audit`

## 변경 이유
- 사용자 요청에 따라 `AGENTS.md`, `work/README.md`, `verify/README.md`, `.pipeline/README.md`를 먼저 다시 읽고, latest Claude `/work`인 `work/3/31/2026-03-31-actual-search-dual-probe-reload-retention.md`와 latest same-day `/verify`인 `verify/3/31/2026-03-31-dual-probe-reload-active-context-retention-verification.md`를 기준으로 이번 라운드 주장만 좁게 검수해야 했습니다.
- latest `/work`는 실제 entity search가 만든 stored record를 `load_web_search_record_id`로 reload했을 때도 dual probe가 `active_context["source_paths"]`에 유지되도록 test-only regression 1건을 추가했다고 적고 있으므로, 이번 검수에서는 그 regression 존재 여부, production 변경 유무, docs sync 필요성, current MVP 범위 일탈 여부, 그리고 필요한 최소 Python regression만 다시 확인하면 충분했습니다.

## 핵심 변경
- 판정: latest `/work`의 code/test 변경 주장은 현재 코드와 일치합니다.
- `tests/test_web_app.py`에는 `test_handle_chat_actual_entity_search_dual_probe_reload_preserves_active_context_source_paths`가 실제로 추가되어 있고, `_FakeWebSearchTool`로 실제 entity search를 한 번 수행해 저장된 `record_id`를 얻은 뒤 `load_web_search_record_id` reload 결과의 `session.active_context.source_paths`에 `boardNo=200`과 `boardNo=300`이 모두 남는지 검증합니다.
- latest `/work`의 `production 코드 변경 없음` 주장도 맞습니다. 이번 round에서 새 production diff는 확인되지 않았고, 현재 동작은 이전 라운드의 `_reuse_web_search_record(... pre_selected_sources=entity_sources ...)` 보정이 실제 search-generated record path에서도 유지되는지 test-only로 잠근 것입니다.
- latest `/work`의 `docs 변경 없음` 주장도 이번 라운드에서는 맞습니다. 이번 수정은 entity-card dual-probe reload family의 service regression 1건을 더 명시적으로 고정한 것이며, root docs가 이 exact retention heuristic을 current shipped contract로 직접 약속하고 있지는 않습니다.
- 범위 역시 현재 projectH 방향에서 벗어나지 않습니다. web investigation remains secondary, read-only, permission-gated, and logged라는 경계 안에서 entity-card reload evidence/source context 정합성만 좁게 검증했고, approval flow, reviewed-memory, UI, Playwright, latest_update/live family, 문서 계약 확장은 확인되지 않았습니다.
- same-family의 다음 smallest shipped-flow risk는 direct history-card `load_web_search_record_id` path가 아니라, 실제 entity search가 만든 record를 자연어 recent-reload(`방금 검색한 결과 다시 보여줘`)로 다시 불러올 때도 같은 dual-probe retention이 유지되는지 explicit regression으로 잠그는 일입니다. 이건 다음 handoff 선정 근거이며, 이번 round의 truth 판정 자체를 바꾸지는 않습니다.
- whole-project audit이 필요한 징후는 아니므로 `report/`는 만들지 않았습니다.

## 검증
- `python3 -m unittest -v tests.test_web_app`
  - 통과 (`Ran 112 tests`, `OK`)
- `git diff --check -- core/agent_loop.py tests/test_web_app.py`
  - 통과 (출력 없음)
- 수동 truth 대조
  - `work/3/31/2026-03-31-actual-search-dual-probe-reload-retention.md`
  - `verify/3/31/2026-03-31-dual-probe-reload-active-context-retention-verification.md`
  - `.pipeline/codex_feedback.md`
  - `docs/TASK_BACKLOG.md`
  - `docs/MILESTONES.md`
  - `docs/NEXT_STEPS.md`
  - `core/agent_loop.py`
  - `tests/test_web_app.py`
- 추가 확인
  - `git diff -- core/agent_loop.py tests/test_web_app.py`
  - `rg -n "recent.*reload|방금 검색한 결과|load_web_search_record_id|reuse_web_search_record|record_id" tests/test_web_app.py tests/test_smoke.py core/agent_loop.py`
  - `sed -n '5750,5970p' core/agent_loop.py`
  - `sed -n '8380,8545p' tests/test_web_app.py`
  - `sed -n '1740,1825p' tests/test_smoke.py`
  - `sed -n '2310,2425p' tests/test_smoke.py`
  - `sed -n '8040,8160p' tests/test_web_app.py`
- 이번 라운드에서 재실행하지 않은 검증
  - `python3 -m unittest -v tests.test_smoke`
  - `make e2e-test`
  - 이유: 이번 변경은 `tests.test_web_app` service regression 1건 추가가 전부인 test-only slice였고, browser-visible markup/CSS나 docs wording 자체는 바뀌지 않았으므로 `tests.test_web_app`과 scoped diff check만으로 직접 영향 범위를 재검수할 수 있었습니다.

## 남은 리스크
- current reload family에서 아직 explicit regression으로 잠기지 않은 shipped surface는, 같은 actual entity search-generated record를 자연어 recent-reload(`방금 검색한 결과 다시 보여줘`)로 다시 불러올 때 dual probe가 `active_context["source_paths"]`에 유지되는지 여부입니다.
- `_reuse_web_search_record()` 내부 구현은 `record_id` 유무와 무관하게 공통이지만, current UI와 service contract는 history-card click뿐 아니라 recent-record recall phrasing도 지원하므로 같은 family의 user-visible reload path 1건을 더 잠그는 가치는 남아 있습니다.
- dirty worktree가 여전히 넓어 다음 검수도 unrelated 변경을 끌어오지 않도록 scoped verification discipline이 계속 필요합니다.
