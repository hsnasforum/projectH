# 2026-03-31 entity-card weak/missing slot natural reload retention verification

## 변경 파일
- `verify/3/31/2026-03-31-entity-card-weak-missing-slot-natural-reload-retention-verification.md`
- `.pipeline/codex_feedback.md`

## 사용 skill
- `round-handoff`
- `investigation-quality-audit`

## 변경 이유
- 사용자 요청에 따라 `AGENTS.md`, `work/README.md`, `verify/README.md`, `.pipeline/README.md`를 먼저 다시 읽고, latest Claude `/work`인 `work/3/31/2026-03-31-entity-card-weak-missing-slot-natural-reload-retention.md`와 latest same-day `/verify`인 `verify/3/31/2026-03-31-entity-card-weak-missing-slot-history-reload-retention-verification.md`를 기준으로 이번 라운드 주장만 좁게 검수해야 했습니다.
- latest `/work`는 자연어 recent-record reload에서 weak/missing slot 구분이 유지되는지 `tests/test_web_app.py` 1건으로 잠그는 test-only slice라고 적고 있으므로, 이번 검수에서는 해당 regression 존재 여부, production/docs 무변경 주장, 현재 MVP 방향 일탈 여부, 그리고 note가 적은 최소 검증만 다시 확인하면 충분했습니다.

## 핵심 변경
- 판정: latest `/work`의 test-only 변경 주장은 현재 코드와 일치합니다.
- `tests/test_web_app.py`에는 `test_handle_chat_entity_card_weak_vs_missing_slot_retained_after_natural_reload`가 실제로 추가되어 있고, 첫 entity search 뒤 `"방금 검색한 결과 다시 보여줘"` 자연어 reload를 호출해 reloaded `response.text`에 `불확실 정보:`와 `추가 확인 필요:`가 모두 남는지, weak section에 `단일 출처` 문구가 있는지, missing section에 `교차 확인 가능한 근거가 더 필요합니다` 문구가 있는지, 그리고 `response.claim_coverage`에 `weak`와 `missing` status가 함께 남는지를 검증합니다.
- 이번 라운드의 production 추가 변경은 없습니다. 직전 history-card reload round에서 들어간 `_reuse_web_search_record()`의 summary reconstruction fix가 자연어 recent-record reload에도 그대로 적용되어, latest `/work`가 적은 대로 이번 round는 test-only follow-up입니다.
- docs 추가 변경도 필요하지 않았습니다. 이번 slice는 현재 shipped weak/missing slot separation contract를 natural reload까지 고정하는 regression 1건이며, `README.md`, `docs/PRODUCT_SPEC.md`, `docs/ACCEPTANCE_CRITERIA.md`가 설명하는 current contract를 넓히지 않습니다.
- 범위도 현재 projectH 방향에서 벗어나지 않습니다. `docs/MILESTONES.md`, `docs/NEXT_STEPS.md`, `docs/TASK_BACKLOG.md`가 가리키는 current phase는 여전히 Milestone 4 secondary-mode investigation hardening이며, 이번 라운드는 그 안의 `single-source fact vs unresolved slot` clarity family를 natural reload path까지 닫는 same-family current-risk reduction 1건입니다.
- whole-project audit이 필요한 징후는 아니므로 `report/`는 만들지 않았습니다.

## 검증
- `python3 -m unittest -v tests.test_web_app`
  - 통과 (`Ran 122 tests`, `OK`)
- `git diff --check -- core/agent_loop.py tests/test_web_app.py`
  - 통과 (출력 없음)
- 수동 truth 대조
  - `work/3/31/2026-03-31-entity-card-weak-missing-slot-natural-reload-retention.md`
  - `verify/3/31/2026-03-31-entity-card-weak-missing-slot-history-reload-retention-verification.md`
  - `.pipeline/codex_feedback.md`
  - `tests/test_web_app.py`
  - `core/agent_loop.py`
  - `docs/MILESTONES.md`
  - `docs/NEXT_STEPS.md`
  - `docs/TASK_BACKLOG.md`
- 이번 라운드에서 재실행하지 않은 검증
  - `python3 -m unittest -v tests.test_smoke`
  - `make e2e-test`
  - 이유: 이번 변경은 `tests/test_web_app.py` regression 1건만 추가한 test-only slice였고, browser-visible 새 contract나 docs/production hunk가 없어서 smoke/e2e까지 다시 돌릴 필요는 없었습니다.

## 남은 리스크
- entity-card weak/missing slot section separation family는 initial response, history-card reload, natural reload 3개 shipped flow에서 모두 explicit regression으로 잠겼습니다. 이 family는 현재 truth 기준으로 닫혔다고 봐도 됩니다.
- 이 상태에서 다음 exact slice는 같은 family 안에서는 더 이상 current-risk reduction으로 바로 이어지지 않습니다. broad Milestone 4 안에서 남은 plausible 후보는 적어도 둘입니다:
  - multi-source agreement / single-source noise 축의 다음 risk slice
  - weak or unresolved slot reinvestigation effectiveness 축의 다음 risk slice
- 두 후보 중 하나를 지금 자동으로 고르면 whole-project 방향 재판정에 가까워지므로, 다음 handoff는 `STATUS: needs_operator`로 두고 operator가 broad axis 1개를 다시 골라 주시는 편이 정직합니다.
