# 2026-03-31 entity-card weak-slot vs missing-slot section regression verification

## 변경 파일
- `verify/3/31/2026-03-31-entity-card-weak-vs-missing-slot-section-regression-verification.md`
- `.pipeline/codex_feedback.md`

## 사용 skill
- `round-handoff`
- `investigation-quality-audit`

## 변경 이유
- 사용자 요청에 따라 `AGENTS.md`, `work/README.md`, `verify/README.md`, `.pipeline/README.md`를 먼저 다시 읽고, latest Claude `/work`인 `work/3/31/2026-03-31-entity-card-weak-vs-missing-slot-section-regression.md`와 latest same-day `/verify`인 `verify/3/31/2026-03-31-zero-strong-slot-history-card-badge-playwright-smoke-verification.md`를 기준으로 이번 라운드 주장만 좁게 검수해야 했습니다.
- latest `/work`는 entity-card 응답 본문에서 weak slot과 missing slot이 서로 다른 섹션으로 유지되는지 `tests/test_web_app.py` 1건으로 잠그는 test-only slice라고 적고 있으므로, 이번 검수에서는 해당 regression 존재 여부, production/docs 무변경 주장, 현재 MVP 방향 일탈 여부, 그리고 note가 적은 최소 검증만 다시 확인하면 충분했습니다.

## 핵심 변경
- 판정: latest `/work`의 test-only 변경 주장은 현재 코드와 일치합니다.
- `tests/test_web_app.py`에는 `test_handle_chat_entity_card_separates_weak_and_missing_slot_sections`가 실제로 추가되어 있고, entity-card 응답 본문에서 `불확실 정보:`와 `추가 확인 필요:` 두 섹션이 모두 존재하는지, weak section에는 `단일 출처` 문구가 남는지, missing section에는 `교차 확인 가능한 근거가 더 필요합니다` 문구가 남는지를 직접 검증합니다.
- 이번 라운드의 production 추가 변경은 없습니다. `core/agent_loop.py`에는 이미 entity-card 본문 조립 시 weak claim을 `불확실 정보:` 아래 `단일 출처` 문구와 함께 렌더링하고, unresolved slot을 `추가 확인 필요:` 아래 `교차 확인 가능한 근거가 더 필요합니다.` 문구로 렌더링하는 로직이 존재합니다.
- docs 추가 변경도 없습니다. 이번 slice는 현재 shipped claim-coverage / uncertainty contract를 web-app regression으로 더 좁게 고정한 test-only follow-up이라, `README.md`, `docs/PRODUCT_SPEC.md`, `docs/ACCEPTANCE_CRITERIA.md`를 다시 넓힐 이유는 없었습니다.
- 범위도 현재 projectH 방향에서 벗어나지 않습니다. `docs/MILESTONES.md`, `docs/NEXT_STEPS.md`, `docs/TASK_BACKLOG.md`가 가리키는 current phase는 여전히 Milestone 4 secondary-mode investigation hardening이며, 이번 라운드는 그 안의 `single-source fact vs unresolved slot` user-visible clarity를 좁게 보강하는 same-family current-risk reduction 1건입니다.
- whole-project audit이 필요한 징후는 아니므로 `report/`는 만들지 않았습니다.

## 검증
- `python3 -m unittest -v tests.test_web_app`
  - 통과 (`Ran 120 tests`, `OK`)
- `git diff --check -- core/agent_loop.py tests/test_web_app.py`
  - 통과 (출력 없음)
- 수동 truth 대조
  - `work/3/31/2026-03-31-entity-card-weak-vs-missing-slot-section-regression.md`
  - `verify/3/31/2026-03-31-zero-strong-slot-history-card-badge-playwright-smoke-verification.md`
  - `.pipeline/codex_feedback.md`
  - `tests/test_web_app.py`
  - `core/agent_loop.py`
  - `docs/MILESTONES.md`
  - `docs/NEXT_STEPS.md`
  - `docs/TASK_BACKLOG.md`
- 이번 라운드에서 재실행하지 않은 검증
  - `python3 -m unittest -v tests.test_smoke`
  - `make e2e-test`
  - 이유: 이번 변경은 `tests/test_web_app.py`의 regression 1건만 추가한 test-only slice였고, browser-visible 새 동작이나 production/docs hunk가 없어서 smoke/e2e까지 다시 돌릴 필요는 없었습니다.

## 남은 리스크
- initial entity-card 응답에서 weak slot과 missing slot을 다른 문구/섹션으로 보여 주는 계약은 이번 라운드로 explicit web-app regression이 생겼습니다.
- 다만 현재 shipped user flow 중 history-card 선택 reload(`load_web_search_record_id`) 경로에서 같은 weak/missing 구분이 summary text와 structured claim coverage에 그대로 남는지는 아직 같은 family의 direct regression으로 잠기지 않았습니다.
- 따라서 다음 smallest same-family current-risk slice는 `entity-card weak-slot vs missing-slot history-card reload exact-field retention only`가 맞습니다. direct history-card reload 1건에 대해 reloaded `response.text`가 두 섹션을 그대로 유지하는지, 그리고 `claim_coverage`에 `weak`/`missing` status가 함께 남는지 `tests/test_web_app.py` 1건으로 잠그는 정도면 충분합니다.
