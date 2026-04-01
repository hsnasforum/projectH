# 2026-03-31 actual-search dual-probe natural reload retention verification

## 변경 파일
- `verify/3/31/2026-03-31-actual-search-dual-probe-natural-reload-retention-verification.md`
- `.pipeline/codex_feedback.md`

## 사용 skill
- `round-handoff`
- `investigation-quality-audit`

## 변경 이유
- 사용자 요청에 따라 `AGENTS.md`, `work/README.md`, `verify/README.md`, `.pipeline/README.md`를 먼저 다시 읽고, latest Claude `/work`인 `work/3/31/2026-03-31-actual-search-dual-probe-natural-reload-retention.md`와 latest same-day `/verify`인 `verify/3/31/2026-03-31-actual-search-dual-probe-reload-retention-verification.md`를 기준으로 이번 라운드 주장만 좁게 검수해야 했습니다.
- latest `/work`는 실제 entity search가 만든 최근 record를 자연어 recent-record recall(`방금 검색한 결과 다시 보여줘`)로 reload했을 때 dual probe가 `active_context["source_paths"]`에 유지되도록 test-only regression 1건을 추가했다고 적고 있으므로, 이번 검수에서는 그 regression 존재 여부, production 변경 유무, docs sync 필요성, current MVP 범위 일탈 여부, 그리고 필요한 최소 Python regression만 다시 확인하면 충분했습니다.

## 핵심 변경
- 판정: latest `/work`의 code/test 변경 주장은 현재 코드와 일치합니다.
- `tests/test_web_app.py`에는 `test_handle_chat_actual_entity_search_dual_probe_natural_reload_preserves_source_paths`가 실제로 추가되어 있고, `_FakeWebSearchTool`로 실제 entity search를 한 번 수행한 뒤 같은 세션에서 `user_text="방금 검색한 결과 다시 보여줘"`를 호출했을 때 `session.active_context.source_paths`에 `boardNo=200`과 `boardNo=300`이 모두 남는지 검증합니다.
- latest `/work`의 `production 코드 변경 없음` 주장도 맞습니다. 이번 round에서 새 production diff는 확인되지 않았고, 현재 동작은 이전 라운드들의 source-selection 및 reload-context 보정이 자연어 recent-record recall path에서도 유지되는지 test-only로 잠근 것입니다.
- latest `/work`의 `docs 변경 없음` 주장도 이번 라운드에서는 맞습니다. 이번 수정은 entity-card dual-probe natural reload family의 service regression 1건을 더 명시적으로 고정한 것이며, root docs가 이 exact retention heuristic을 current shipped contract로 직접 약속하고 있지는 않습니다.
- 범위 역시 현재 projectH 방향에서 벗어나지 않습니다. web investigation remains secondary, read-only, permission-gated, and logged라는 경계 안에서 entity-card recent-record reload evidence/source context 정합성만 좁게 검증했고, approval flow, reviewed-memory, UI, Playwright, latest_update/live family, 문서 계약 확장은 확인되지 않았습니다.
- same-family의 다음 smallest shipped-flow risk는 source path retention 자체가 아니라, 같은 actual entity search natural reload path에서 `response_origin.answer_mode`, `verification_label`, `source_roles`, `web_search_record_path` 같은 user-visible badge/meta exact field가 initial과 일관되게 유지되는지 explicit regression으로 잠그는 일입니다. latest_update 쪽은 이미 natural reload exact-field regression이 있지만, entity-card actual-search natural reload family는 아직 그 path를 명시적으로 잠그지 않았습니다.
- whole-project audit이 필요한 징후는 아니므로 `report/`는 만들지 않았습니다.

## 검증
- `python3 -m unittest -v tests.test_web_app`
  - 통과 (`Ran 113 tests`, `OK`)
- `git diff --check -- core/agent_loop.py tests/test_web_app.py`
  - 통과 (출력 없음)
- 수동 truth 대조
  - `work/3/31/2026-03-31-actual-search-dual-probe-natural-reload-retention.md`
  - `verify/3/31/2026-03-31-actual-search-dual-probe-reload-retention-verification.md`
  - `.pipeline/codex_feedback.md`
  - `docs/TASK_BACKLOG.md`
  - `docs/MILESTONES.md`
  - `docs/NEXT_STEPS.md`
  - `core/agent_loop.py`
  - `tests/test_web_app.py`
  - `tests/test_smoke.py`
- 추가 확인
  - `git diff -- core/agent_loop.py tests/test_web_app.py`
  - `rg -n "test_handle_chat_actual_entity_search_dual_probe_natural_reload_preserves_source_paths|방금 검색한 결과 다시 보여줘|boardNo=200|boardNo=300|load_web_search_record_id" tests/test_web_app.py core/agent_loop.py`
  - `rg -n "entity-card|entity card|web investigation|history-card|다시 불러오기|recent-record|reload" docs/TASK_BACKLOG.md docs/MILESTONES.md docs/NEXT_STEPS.md`
  - `rg -n "entity card|entity_card|설명 카드|verification_label|source_roles|백과 기반|공식 기반|방금 검색한 결과 다시 보여줘" tests/test_web_app.py tests/test_smoke.py`
  - `sed -n '8460,8575p' tests/test_web_app.py`
  - `sed -n '5830,5965p' core/agent_loop.py`
  - `sed -n '7960,8395p' tests/test_web_app.py`
  - `sed -n '2280,2388p' tests/test_smoke.py`
  - `sed -n '1860,1915p' tests/test_smoke.py`
  - `sed -n '5390,5435p' tests/test_web_app.py`
  - `sed -n '5600,5735p' tests/test_web_app.py`
- 이번 라운드에서 재실행하지 않은 검증
  - `python3 -m unittest -v tests.test_smoke`
  - `make e2e-test`
  - 이유: 이번 변경은 `tests.test_web_app` service regression 1건 추가가 전부인 test-only slice였고, browser-visible markup/CSS나 docs wording 자체는 바뀌지 않았으므로 `tests.test_web_app`과 scoped diff check만으로 직접 영향 범위를 재검수할 수 있었습니다.

## 남은 리스크
- current actual-search natural reload family에서 아직 explicit regression으로 잠기지 않은 shipped surface는, 같은 natural recent-record recall path에서 `response_origin.answer_mode`, `verification_label`, `source_roles`, `web_search_record_path` 같은 user-visible badge/meta exact field가 initial entity-card result와 일관되게 유지되는지 여부입니다.
- source path retention은 이번 round에서 닫혔지만, current UI와 service contract는 reload 뒤 answer-mode badge와 source-role/verification metadata도 함께 노출하므로 same-family exact-field regression 1건을 더 잠그는 가치는 남아 있습니다.
- dirty worktree가 여전히 넓어 다음 검수도 unrelated 변경을 끌어오지 않도록 scoped verification discipline이 계속 필요합니다.
