# 2026-03-31 entity probe same-domain selection fix verification

## 변경 파일
- `verify/3/31/2026-03-31-entity-probe-same-domain-selection-fix-verification.md`
- `.pipeline/codex_feedback.md`

## 사용 skill
- `round-handoff`
- `investigation-quality-audit`

## 변경 이유
- 사용자 요청에 따라 `AGENTS.md`, `work/README.md`, `verify/README.md`, `.pipeline/README.md`를 먼저 다시 읽고, latest Claude `/work`인 `work/3/31/2026-03-31-entity-probe-same-domain-selection-fix.md`와 latest same-day `/verify`인 `verify/3/31/2026-03-31-non-object-json-400-regression-verification.md`를 기준으로 이번 라운드 주장만 좁게 검수해야 했습니다.
- latest `/work`는 entity-card web investigation quality 축 안에서 same-domain generic official 때문에 slot-targeted official probe가 hostname dedupe에 막히는 current-risk 1건만 줄였다고 적고 있으므로, 이번 검수에서는 해당 selection 보정과 새 smoke regression 존재 여부, docs sync 필요성, current MVP 범위 일탈 여부, 그리고 필요한 최소 Python regression만 다시 확인하면 충분했습니다.

## 핵심 변경
- 판정: latest `/work`의 code/test 변경 주장은 현재 코드와 일치합니다.
- `core/agent_loop.py`에는 entity `query_profile` selection 경로에서 `evicted_source_ids`를 도입하고, same-domain probe(`probe_bonus > 0`)가 이미 선택된 generic official을 대체할 수 있도록 한 로직이 실제로 들어가 있습니다. 이 로직은 same-domain duplicate를 전면 허용하지 않고, probe와 generic official이 충돌하는 좁은 경우만 다룹니다.
- `tests/test_smoke.py`에는 `test_web_search_entity_probe_replaces_same_domain_generic_official`가 실제로 추가되어 있고, `pearlabyss.com` generic overview(`boardNo=100`)와 platform probe(`boardNo=200`)가 함께 있을 때 probe가 선택되고 generic overview는 탈락하는지 검증합니다.
- latest `/work`가 `docs 변경 없음`이라고 적은 것도 이번 라운드에서는 맞습니다. root docs는 entity-card ranking heuristic의 exact same-domain replacement policy까지 current shipped contract로 약속하지 않고, 현재 round는 secondary-mode web investigation quality 내부의 selection 보정 1건이기 때문입니다.
- 범위도 현재 projectH 방향에서 벗어나지 않습니다. web investigation remains secondary, read-only, permission-gated, and logged라는 invariant 안에서 entity-card missing-slot reinvestigation 품질만 좁게 보정했고, approval flow, reviewed-memory, latest-update/live ranking, UI, Playwright, product contract wording 확장은 확인되지 않았습니다.
- same-family current-risk 기준으로도 맞습니다. 직전 handoff가 지시한 exact slice를 그대로 구현했고, current round의 residual risk도 같은 same-domain probe family 안에 남아 있습니다.
- whole-project audit이 필요한 징후는 아니므로 `report/`는 만들지 않았습니다.

## 검증
- `python3 -m unittest -v tests.test_smoke`
  - 통과 (`Ran 92 tests`, `OK`)
- `python3 -m unittest -v tests.test_web_app`
  - 통과 (`Ran 110 tests`, `OK`)
- `git diff --check -- core/agent_loop.py tests/test_smoke.py`
  - 통과 (출력 없음)
- 수동 truth 대조
  - `work/3/31/2026-03-31-entity-probe-same-domain-selection-fix.md`
  - `verify/3/31/2026-03-31-non-object-json-400-regression-verification.md`
  - `.pipeline/codex_feedback.md`
  - `docs/TASK_BACKLOG.md`
  - `docs/MILESTONES.md`
  - `docs/NEXT_STEPS.md`
  - `core/agent_loop.py`
  - `tests/test_smoke.py`
- 추가 확인
  - `git diff -- core/agent_loop.py tests/test_smoke.py`
  - `rg -n "test_web_search_entity_probe_replaces_same_domain_generic_official|evicted_source_ids|probe_bonus > 0|hostname dedupe|same-domain" core/agent_loop.py tests/test_smoke.py`
  - `stat -c '%y %n' core/agent_loop.py tests/test_smoke.py work/3/31/2026-03-31-entity-probe-same-domain-selection-fix.md`
  - `rg -n "entity-card missing-slot official probe|same-domain|probe replaces|official probe|reinvestigate weak or unresolved slots" .pipeline/codex_feedback.md work/3/31/2026-03-31-entity-probe-same-domain-selection-fix.md docs/TASK_BACKLOG.md docs/MILESTONES.md docs/NEXT_STEPS.md`
- 이번 라운드에서 재실행하지 않은 검증
  - `make e2e-test`
  - 이유: 이번 변경은 `core/agent_loop.py` entity-card source selection과 `tests/test_smoke.py` regression 1건을 중심으로 한 backend ranking slice였고, browser-visible UI contract이나 docs contract wording 자체는 바뀌지 않았으므로 Python regression과 scoped diff check만으로 직접 영향 범위를 재검수할 수 있었습니다.

## 남은 리스크
- latest `/work`가 적은 대로, 같은 도메인의 probe 두 개가 서로 다른 slot을 메우는 경우에는 첫 probe만 유지되고 둘째 probe는 아직 selection에 공존하지 못합니다.
- 따라서 same-domain probe family 안의 다음 smallest current-risk는 "different-slot dual probe coexistence" 쪽으로 남아 있습니다.
- dirty worktree가 여전히 넓어 다음 검수도 unrelated 변경을 건드리지 않는 좁은 범위 통제가 필요합니다.
