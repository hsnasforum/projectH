# 2026-03-31 entity-card weak/missing slot history-card reload retention verification

## 변경 파일
- `verify/3/31/2026-03-31-entity-card-weak-missing-slot-history-reload-retention-verification.md`
- `.pipeline/codex_feedback.md`

## 사용 skill
- `round-handoff`
- `investigation-quality-audit`

## 변경 이유
- 사용자 요청에 따라 `AGENTS.md`, `work/README.md`, `verify/README.md`, `.pipeline/README.md`를 먼저 다시 읽고, latest Claude `/work`인 `work/3/31/2026-03-31-entity-card-weak-missing-slot-history-reload-retention.md`와 latest same-day `/verify`인 `verify/3/31/2026-03-31-entity-card-weak-vs-missing-slot-section-regression-verification.md`를 기준으로 이번 라운드 주장만 좁게 검수해야 했습니다.
- latest `/work`는 history-card reload에서 entity-card formatted summary가 generic summary로 무너지는 실제 버그를 고치고, 같은 reload 경로에서 weak/missing slot 구분이 유지되는지 `tests/test_web_app.py` 1건으로 잠그는 slice라고 적고 있으므로, 이번 검수에서는 해당 production hunk 존재 여부, regression 존재 여부, docs 무변경 주장, 현재 MVP 방향 일탈 여부, 그리고 note가 적은 최소 검증만 다시 확인하면 충분했습니다.

## 핵심 변경
- 판정: latest `/work`의 production/test 변경 주장은 현재 코드와 일치합니다.
- `core/agent_loop.py`의 `_reuse_web_search_record()`는 저장된 `response_origin.answer_mode`를 `stored_answer_mode`로 읽고, entity-card일 때 `stored_intent_kind = "external_fact"`를 유도한 뒤 `_summarize_web_search_results(..., intent_kind=stored_intent_kind, answer_mode=stored_answer_mode or None)`로 전달합니다. 이 hunk로 record reload 경로에서도 entity-card summary formatter가 다시 사용됩니다.
- `tests/test_web_app.py`에는 `test_handle_chat_entity_card_weak_vs_missing_slot_retained_after_history_card_reload`가 실제로 추가되어 있고, 첫 entity search 뒤 `load_web_search_record_id` history-card reload를 호출해 reloaded `response.text`에 `불확실 정보:`와 `추가 확인 필요:`가 모두 남는지, weak section에 `단일 출처` 문구가 있는지, missing section에 `교차 확인 가능한 근거가 더 필요합니다` 문구가 있는지, 그리고 `response.claim_coverage`에 `weak`와 `missing` status가 함께 남는지를 검증합니다.
- docs 추가 변경은 필요하지 않았습니다. 현재 root docs는 이미 claim coverage, answer-mode badge, history-card reload retention을 현재 shipped contract로 설명하고 있고, 이번 round는 그 contract를 넓힌 것이 아니라 reload bug를 복구한 것입니다.
- 범위도 현재 projectH 방향에서 벗어나지 않습니다. `docs/MILESTONES.md`, `docs/NEXT_STEPS.md`, `docs/TASK_BACKLOG.md`가 가리키는 current phase는 여전히 Milestone 4 secondary-mode investigation hardening이며, 이번 라운드는 그 안의 `single-source fact vs unresolved slot` clarity 축에서 shipped reload flow risk를 줄이는 1건입니다.
- whole-project audit이 필요한 징후는 아니므로 `report/`는 만들지 않았습니다.

## 검증
- `python3 -m unittest -v tests.test_web_app`
  - 통과 (`Ran 121 tests`, `OK`)
- `git diff --check -- core/agent_loop.py tests/test_web_app.py`
  - 통과 (출력 없음)
- 수동 truth 대조
  - `work/3/31/2026-03-31-entity-card-weak-missing-slot-history-reload-retention.md`
  - `verify/3/31/2026-03-31-entity-card-weak-vs-missing-slot-section-regression-verification.md`
  - `.pipeline/codex_feedback.md`
  - `core/agent_loop.py`
  - `tests/test_web_app.py`
  - `README.md`
  - `docs/PRODUCT_SPEC.md`
  - `docs/ACCEPTANCE_CRITERIA.md`
  - `docs/MILESTONES.md`
  - `docs/NEXT_STEPS.md`
  - `docs/TASK_BACKLOG.md`
- 이번 라운드에서 재실행하지 않은 검증
  - `python3 -m unittest -v tests.test_smoke`
  - `make e2e-test`
  - 이유: 이번 변경은 web investigation reload service path의 production hunk 1건과 `tests/test_web_app.py` regression 1건에 국한되어 있었고, browser-visible 새 contract 추가나 docs 변경이 없어서 smoke/e2e까지 다시 돌릴 필요는 없었습니다.

## 남은 리스크
- initial entity-card 응답과 direct history-card reload에서 weak slot과 missing slot을 다른 섹션/문구로 유지하는 계약은 이제 explicit regression으로 잠겼습니다.
- 다만 같은 `_reuse_web_search_record()`를 쓰는 자연어 recent-record reload(`방금 검색한 결과 다시 보여줘`) 경로에서 weak/missing section 분리와 `claim_coverage` weak/missing status가 그대로 남는지는 아직 direct regression이 없습니다.
- 따라서 다음 smallest same-family current-risk slice는 `entity-card weak-slot vs missing-slot natural reload exact-field retention only`가 맞습니다. 실제 entity search 뒤 자연어 recent-record reload 1건에 대해 reloaded `response.text`의 두 섹션과 `response.claim_coverage`의 `weak`/`missing` 동시 존재를 `tests/test_web_app.py` 1건으로 고정하는 정도면 충분합니다.
