# 2026-03-31 dual-probe active-context source-path fix verification

## 변경 파일
- `verify/3/31/2026-03-31-dual-probe-active-context-source-path-fix-verification.md`
- `.pipeline/codex_feedback.md`

## 사용 skill
- `round-handoff`
- `investigation-quality-audit`

## 변경 이유
- 사용자 요청에 따라 `AGENTS.md`, `work/README.md`, `verify/README.md`, `.pipeline/README.md`를 먼저 다시 읽고, latest Claude `/work`인 `work/3/31/2026-03-31-dual-probe-active-context-source-path-fix.md`와 latest same-day `/verify`인 `verify/3/31/2026-03-31-entity-dual-probe-same-domain-coexistence-verification.md`를 기준으로 이번 라운드 주장만 좁게 검수해야 했습니다.
- latest `/work`는 entity-card dual probe coexistence가 `selected_source_paths`뿐 아니라 실제 user-visible evidence/source context인 `active_context["source_paths"]`에도 유지되도록 맞췄다고 적고 있으므로, 이번 검수에서는 해당 production 변경, smoke regression 갱신, docs sync 필요성, current MVP 범위 일탈 여부, 그리고 필요한 최소 Python regression만 다시 확인하면 충분했습니다.

## 핵심 변경
- 판정: latest `/work`의 code/test 변경 주장은 현재 코드와 일치합니다.
- `core/agent_loop.py`의 `_build_web_search_active_context()`에는 `pre_selected_sources` optional parameter가 실제로 추가되어 있고, 전달되면 내부 `_select_ranked_web_sources(... max_items=5)` 재선택을 건너뛰고 그 리스트를 그대로 `selected_sources`로 사용합니다.
- 같은 파일의 entity-card handle 경로에서는 `entity_sources`를 미리 `None`으로 초기화한 뒤, entity query에서 `_select_ranked_web_sources(... max_items=3)` 결과를 `entity_sources`에 담고, 이후 `_build_web_search_active_context(... pre_selected_sources=entity_sources, ...)`로 넘겨 claim-selection 결과와 active-context source list가 같은 selection을 공유하도록 바뀌었습니다.
- `tests/test_smoke.py`의 `test_web_search_entity_dual_probe_different_slots_coexist_on_same_domain`는 실제로 `response.selected_source_paths`가 아니라 `response.active_context["source_paths"]`를 검증하도록 바뀌었고, service probe fixture 문구도 `"운영하는 게임"` / `"운영하는 게임이며 배급도..."`으로 조정되어 service/distribution slot 매칭이 명확해졌습니다.
- latest `/work`의 `docs 변경 없음` 주장도 이번 라운드에서는 맞습니다. 이번 수정은 entity-card evidence/source context와 selection 결과를 일치시키는 좁은 investigation heuristic 보정 1건이며, root docs가 exact same-domain dual-probe source-path alignment까지 current shipped contract로 약속하고 있지는 않습니다.
- 범위 역시 현재 projectH 방향에서 벗어나지 않습니다. web investigation remains secondary, read-only, permission-gated, and logged라는 경계 안에서 entity-card evidence/source context 정합성만 좁게 보정했고, approval flow, reviewed-memory, UI, Playwright, latest_update/live family, 문서 계약 확장은 확인되지 않았습니다.
- 다만 same-family 현재 리스크는 하나 남아 있습니다. `_reuse_web_search_record()`의 entity-card reload 경로는 여전히 `_build_web_search_active_context()`를 `pre_selected_sources` 없이 호출하므로, 코드 구조상 initial entity-card path에서 방금 닫은 불일치가 reload path에는 그대로 남아 있다고 보는 편이 맞습니다. 이 판단은 다음 슬라이스 선정 근거이며, 이번 round의 truth 판정 자체를 바꾸지는 않습니다.
- whole-project audit이 필요한 징후는 아니므로 `report/`는 만들지 않았습니다.

## 검증
- `python3 -m unittest -v tests.test_smoke`
  - 통과 (`Ran 93 tests`, `OK`)
- `python3 -m unittest -v tests.test_web_app`
  - 통과 (`Ran 110 tests`, `OK`)
- `git diff --check -- core/agent_loop.py tests/test_smoke.py`
  - 통과 (출력 없음)
- 수동 truth 대조
  - `work/3/31/2026-03-31-dual-probe-active-context-source-path-fix.md`
  - `verify/3/31/2026-03-31-entity-dual-probe-same-domain-coexistence-verification.md`
  - `.pipeline/codex_feedback.md`
  - `docs/TASK_BACKLOG.md`
  - `docs/MILESTONES.md`
  - `docs/NEXT_STEPS.md`
  - `core/agent_loop.py`
  - `tests/test_smoke.py`
- 추가 확인
  - `git diff -- core/agent_loop.py tests/test_smoke.py`
  - `rg -n "active_context.*source_paths|test_web_search_entity_dual_probe_different_slots_coexist_on_same_domain|boardNo=200|boardNo=300|source_paths\\]\\[:3\\]" tests/test_smoke.py core/agent_loop.py`
  - `rg -n "dual_probe|dual-probe|boardNo=300|active_context\\[\\\"source_paths\\\"\\]|load_web_search_record|recent_web_search_record|reload" tests/test_smoke.py tests/test_web_app.py core/agent_loop.py`
  - `sed -n '5208,5268p' core/agent_loop.py`
  - `sed -n '5638,5745p' core/agent_loop.py`
  - `sed -n '5878,5968p' core/agent_loop.py`
  - `sed -n '1635,1715p' tests/test_smoke.py`
  - `stat -c '%y %n' core/agent_loop.py tests/test_smoke.py work/3/31/2026-03-31-dual-probe-active-context-source-path-fix.md verify/3/31/2026-03-31-entity-dual-probe-same-domain-coexistence-verification.md .pipeline/codex_feedback.md`
- 이번 라운드에서 재실행하지 않은 검증
  - `make e2e-test`
  - 이유: 이번 변경은 `core/agent_loop.py`의 entity-card active-context source selection 정합성과 `tests/test_smoke.py` regression 1건을 중심으로 한 backend investigation slice였고, browser selector/markup/CSS나 docs wording 자체는 바뀌지 않았으므로 Python regression과 scoped diff check만으로 직접 영향 범위를 재검수할 수 있었습니다.

## 남은 리스크
- `_reuse_web_search_record()`의 entity-card reload 경로는 여전히 `_build_web_search_active_context()`를 `pre_selected_sources` 없이 호출합니다. 따라서 같은 same-family current-risk가 history reload surface에는 남아 있을 가능성이 높고, 다음 smallest slice는 reload 후 `active_context["source_paths"]`에도 dual probe 공존이 유지되는지 focused regression으로 잠그는 일입니다.
- non-entity path는 여전히 기존 독립 selection을 유지하며, 이번 round는 그 경로를 넓히지 않았습니다.
- 같은 파일들에 이전 round dirty hunk가 누적되어 있어, 다음 검수도 unrelated 변경을 끌어오지 않도록 scoped verification discipline이 계속 필요합니다.
