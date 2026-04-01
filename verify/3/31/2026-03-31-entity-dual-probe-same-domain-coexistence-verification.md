# 2026-03-31 entity dual probe same-domain coexistence verification

## 변경 파일
- `verify/3/31/2026-03-31-entity-dual-probe-same-domain-coexistence-verification.md`
- `.pipeline/codex_feedback.md`

## 사용 skill
- `round-handoff`
- `investigation-quality-audit`

## 변경 이유
- 사용자 요청에 따라 `AGENTS.md`, `work/README.md`, `verify/README.md`, `.pipeline/README.md`를 먼저 다시 읽고, latest Claude `/work`인 `work/3/31/2026-03-31-entity-dual-probe-same-domain-coexistence.md`와 latest same-day `/verify`인 `verify/3/31/2026-03-31-entity-probe-same-domain-selection-fix-verification.md`를 기준으로 이번 라운드 주장만 좁게 검수해야 했습니다.
- latest `/work`는 entity-card web investigation quality 축 안에서 "같은 official domain의 서로 다른 slot-targeted probe 두 개가 hostname dedupe에 막히지 않고 공존해야 한다"는 current-risk 1건만 줄였다고 적고 있으므로, 이번 검수에서는 해당 selection 로직과 새 smoke regression 존재 여부, current MVP 범위 일탈 여부, 그리고 필요한 최소 Python regression만 다시 확인하면 충분했습니다.

## 핵심 변경
- 판정: latest `/work`의 code/test 변경 주장은 현재 코드와 일치합니다.
- `core/agent_loop.py`의 entity-card selection `_push()` 경로에는 same-domain 후보가 이미 선택된 상태에서도 `probe_bonus > 0`인 probe끼리는 `_entity_slot_from_search_query()`로 slot을 비교해, 서로 다른 slot이면 공존을 허용하고 같은 slot이면 계속 차단하는 로직이 실제로 들어가 있습니다.
- `tests/test_smoke.py`에는 `test_web_search_entity_dual_probe_different_slots_coexist_on_same_domain`가 실제로 추가되어 있고, 같은 `pearlabyss.com` 도메인에서 platform probe(`boardNo=200`)와 service probe(`boardNo=300`)가 함께 선택되어 `response.selected_source_paths`에 공존하는지 검증합니다.
- latest `/work`의 `docs 변경 없음` 주장도 이번 라운드에서는 맞습니다. 이번 변경은 secondary-mode entity-card ranking heuristic의 좁은 same-domain probe coexistence 보정 1건이며, root docs가 exact hostname-dedupe 예외 규칙까지 current shipped contract로 약속하고 있지는 않습니다.
- 범위 역시 현재 projectH 방향에서 벗어나지 않습니다. web investigation remains secondary, read-only, permission-gated, and logged라는 경계 안에서 entity-card slot reinvestigation 품질만 좁게 보정했고, approval flow, reviewed-memory, UI, Playwright, latest_update/live family, 문서 계약 확장은 확인되지 않았습니다.
- same files(`core/agent_loop.py`, `tests/test_smoke.py`)에는 같은 날 이전 round들의 미커밋 변경도 함께 남아 있지만, latest `/work`가 주장한 이번 round의 specific hunk와 regression은 그 안에서 분리해 확인했습니다.
- whole-project audit이 필요한 징후는 아니므로 `report/`는 만들지 않았습니다.

## 검증
- `python3 -m unittest -v tests.test_smoke`
  - 통과 (`Ran 93 tests`, `OK`)
- `python3 -m unittest -v tests.test_web_app`
  - 통과 (`Ran 110 tests`, `OK`)
- `git diff --check -- core/agent_loop.py tests/test_smoke.py`
  - 통과 (출력 없음)
- 수동 truth 대조
  - `work/3/31/2026-03-31-entity-dual-probe-same-domain-coexistence.md`
  - `verify/3/31/2026-03-31-entity-probe-same-domain-selection-fix-verification.md`
  - `.pipeline/codex_feedback.md`
  - `docs/TASK_BACKLOG.md`
  - `docs/MILESTONES.md`
  - `docs/NEXT_STEPS.md`
  - `core/agent_loop.py`
  - `tests/test_smoke.py`
- 추가 확인
  - `rg -n "test_web_search_entity_dual_probe_different_slots_coexist_on_same_domain|_entity_slot_from_search_query|probe_bonus|same-domain|coexist" core/agent_loop.py tests/test_smoke.py`
  - `sed -n '1510,1615p' tests/test_smoke.py`
  - `sed -n '1619,1715p' tests/test_smoke.py`
  - `sed -n '4700,4805p' core/agent_loop.py`
  - `sed -n '5206,5268p' core/agent_loop.py`
  - `sed -n '8310,8388p' tests/test_web_app.py`
  - `git diff -- core/agent_loop.py tests/test_smoke.py`
  - `stat -c '%y %n' core/agent_loop.py tests/test_smoke.py work/3/31/2026-03-31-entity-dual-probe-same-domain-coexistence.md verify/3/31/2026-03-31-entity-probe-same-domain-selection-fix-verification.md .pipeline/codex_feedback.md`
- 이번 라운드에서 재실행하지 않은 검증
  - `make e2e-test`
  - 이유: 이번 변경은 `core/agent_loop.py` entity-card source selection과 `tests/test_smoke.py` regression 1건을 중심으로 한 backend ranking slice였고, browser-visible UI contract나 docs wording 자체는 바뀌지 않았으므로 Python regression과 scoped diff check만으로 직접 영향 범위를 재검수할 수 있었습니다.

## 남은 리스크
- 이번 round는 dual probe coexistence를 `response.selected_source_paths` 기준으로만 고정했습니다. 그러나 user-visible evidence/source context는 `_build_web_search_active_context(... max_items=5)`의 별도 selection pass를 거치므로, 같은 fixture에서 `response.active_context["source_paths"]`까지 둘 다 유지되는지는 아직 explicit regression으로 잠겨 있지 않습니다.
- same-slot same-domain duplicate probe는 여전히 의도적으로 차단되며, 이번 round는 그 정책을 바꾸지 않았습니다.
- 같은 파일들에 이전 round dirty hunk가 누적되어 있어, 다음 검수도 unrelated 변경을 끌어오지 않도록 scoped verification discipline이 계속 필요합니다.
