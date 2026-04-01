# 2026-03-31 dual-probe history-card reload exact-field retention verification

## 변경 파일
- `verify/3/31/2026-03-31-dual-probe-history-card-reload-exact-field-retention-verification.md`
- `.pipeline/codex_feedback.md`

## 사용 skill
- `round-handoff`
- `investigation-quality-audit`

## 변경 이유
- 사용자 요청에 따라 `AGENTS.md`, `work/README.md`, `verify/README.md`, `.pipeline/README.md`를 먼저 다시 읽고, latest Claude `/work`인 `work/3/31/2026-03-31-dual-probe-history-card-reload-exact-field-retention.md`와 latest same-day `/verify`인 `verify/3/31/2026-03-31-dual-probe-natural-reload-exact-field-retention-verification.md`를 기준으로 이번 라운드 주장만 좁게 검수해야 했습니다.
- latest `/work`는 actual dual-probe entity search가 만든 record를 history-card 선택 경로(`load_web_search_record_id`)로 reload했을 때 `response_origin.answer_mode`, `verification_label`, `source_roles`, `web_search_record_path` exact field가 initial과 일관되게 유지되는 test-only regression 1건을 추가했다고 적고 있으므로, 이번 검수에서는 그 regression 존재 여부, production 변경 유무, docs sync 필요성, current MVP 범위 일탈 여부, 그리고 필요한 최소 Python regression만 다시 확인하면 충분했습니다.

## 핵심 변경
- 판정: latest `/work`의 code/test 변경 주장은 현재 코드와 일치합니다.
- `tests/test_web_app.py`에는 `test_handle_chat_dual_probe_entity_search_history_card_reload_exact_fields`가 실제로 추가되어 있고, `_FakeWebSearchTool`로 actual dual-probe entity search를 한 번 수행해 `record_id`와 initial `response_origin`, `web_search_record_path`를 확보한 뒤 같은 세션에서 `load_web_search_record_id` history-card reload를 호출했을 때 `answer_mode`, `verification_label`, `source_roles`, `web_search_record_path`가 initial과 일관되는지 검증합니다.
- latest `/work`의 `production 코드 변경 없음` 주장도 맞습니다. 이번 round에서 새 production diff는 확인되지 않았고, 현재 동작은 이전 reload-related 변경 위에 history-card dual-probe exact-field regression 1건만 추가한 test-only slice입니다.
- latest `/work`의 `docs 변경 없음` 주장도 이번 라운드에서는 맞습니다. 이번 수정은 이미 shipped된 entity-card reload behavior의 exact-field retention regression 1건을 더 잠근 것이고, root docs가 이 exact history-card reload heuristic을 current shipped contract로 직접 약속하고 있지는 않습니다.
- 범위 역시 현재 projectH 방향에서 벗어나지 않습니다. web investigation remains secondary, read-only, permission-gated, and logged라는 경계 안에서 entity-card history-card reload badge/meta 정합성만 좁게 검증했고, approval flow, reviewed-memory, latest_update/live family, UI, Playwright, 문서 계약 확장은 확인되지 않았습니다.
- latest `/work`가 적은 대로 entity-card reload exact-field family는 single-source(자연어+history-card)와 dual-probe(자연어+history-card) 4개 경로가 모두 explicit regression으로 잠긴 상태가 맞습니다. current local truth 기준으로 같은 family 안에서 더 작은 current-risk slice를 자동으로 고르는 것은 정직하지 않으므로, 다음 handoff는 새 quality axis를 임의로 열지 않고 `STATUS: needs_operator`로 멈추는 편이 맞습니다.
- whole-project audit이 필요한 징후는 아니므로 `report/`는 만들지 않았습니다.

## 검증
- `python3 -m unittest -v tests.test_web_app`
  - 통과 (`Ran 116 tests`, `OK`)
- `git diff --check -- core/agent_loop.py tests/test_web_app.py`
  - 통과 (출력 없음)
- 수동 truth 대조
  - `AGENTS.md`
  - `work/README.md`
  - `verify/README.md`
  - `.pipeline/README.md`
  - `work/3/31/2026-03-31-dual-probe-history-card-reload-exact-field-retention.md`
  - `verify/3/31/2026-03-31-dual-probe-natural-reload-exact-field-retention-verification.md`
  - `.pipeline/codex_feedback.md`
  - `docs/TASK_BACKLOG.md`
  - `docs/MILESTONES.md`
  - `tests/test_web_app.py`
- 추가 확인
  - `sed -n '8738,8818p' tests/test_web_app.py`
  - `rg -n "test_handle_chat_dual_probe_entity_search_history_card_reload_exact_fields|load_web_search_record_id|verification_label|source_roles|web_search_record_path" tests/test_web_app.py`
- 이번 라운드에서 재실행하지 않은 검증
  - `python3 -m unittest -v tests.test_smoke`
  - `make e2e-test`
  - 이유: 이번 변경은 `tests.test_web_app` service regression 1건 추가가 전부인 test-only slice였고, browser-visible markup/CSS나 docs wording 자체는 바뀌지 않았으므로 `tests.test_web_app`과 scoped diff check만으로 직접 영향 범위를 재검수할 수 있었습니다.

## 남은 리스크
- entity-card reload exact-field family 자체는 이번 라운드로 truthfully 닫혔습니다. 따라서 다음 자동 slice는 같은 family의 completeness work가 아니라, operator가 Milestone 4 entity-card web investigation quality 축 안에서 다음 user-visible/current-risk slice 1개를 새로 정해야 합니다.
- dirty worktree가 여전히 넓어 다음 검수도 unrelated 변경을 끌어오지 않도록 scoped verification discipline이 계속 필요합니다.
