# 2026-03-31 entity-card zero-strong-slot verification badge downgrade verification

## 변경 파일
- `verify/3/31/2026-03-31-entity-card-zero-strong-slot-badge-downgrade-verification.md`
- `.pipeline/codex_feedback.md`

## 사용 skill
- `round-handoff`
- `investigation-quality-audit`

## 변경 이유
- 사용자 요청에 따라 `AGENTS.md`, `work/README.md`, `verify/README.md`, `.pipeline/README.md`를 먼저 다시 읽고, latest Claude `/work`인 `work/3/31/2026-03-31-entity-card-zero-strong-slot-badge-downgrade.md`와 latest same-day `/verify`인 `verify/3/31/2026-03-31-dual-probe-history-card-reload-exact-field-retention-verification.md`를 기준으로 이번 라운드 주장만 좁게 검수해야 했습니다.
- latest `/work`는 entity-card에서 `claim_coverage`에 `strong` 슬롯이 0개일 때 header verification badge가 과장되지 않도록 production/test/docs를 함께 갱신했다고 적고 있으므로, 이번 검수에서는 해당 hunk 존재 여부, docs sync truth, current MVP 방향 일탈 여부, 그리고 note가 요구한 최소 검증만 다시 확인하면 충분했습니다.

## 핵심 변경
- 판정: latest `/work`의 production/test/docs 변경 주장은 현재 파일과 일치합니다.
- `core/agent_loop.py`에는 `_build_web_search_origin()`과 `_build_web_verification_label()`에 `claim_coverage` optional parameter가 실제로 추가되어 있고, entity-card에서 `strong_reference_count >= 2`여도 `claim_coverage`에 `status == "strong"` 슬롯이 없으면 `설명형 다중 출처 합의`를 주지 않도록 보정되어 있습니다.
- initial search 경로와 reload 경로 모두 `_build_web_search_origin(..., claim_coverage=claim_coverage)`를 호출하므로, latest `/work`의 "initial + reload 둘 다 전달" 주장도 맞습니다.
- `tests/test_smoke.py`에는 `test_entity_card_zero_strong_slot_downgrades_verification_label`가 실제로 추가되어 있고, wiki 2개가 있어도 `claim_coverage`에 strong 슬롯이 0개면 `response_origin.verification_label != "설명형 다중 출처 합의"`를 검증합니다.
- docs sync도 실제로 들어가 있습니다. `README.md`, `docs/PRODUCT_SPEC.md`, `docs/ACCEPTANCE_CRITERIA.md`는 entity-card verification badge가 no-strong-slot일 때 strong으로 과장되지 않는다는 현재 shipped truth를 반영합니다.
- 범위도 현재 projectH 방향에서 벗어나지 않습니다. 이 변경은 secondary-mode web investigation의 strong/weak/unresolved 분리 정확도를 높이는 current-risk reduction 1건이며, approval flow, reviewed-memory, latest-update family, broad UI expansion은 포함하지 않았습니다.
- whole-project audit이 필요한 징후는 아니므로 `report/`는 만들지 않았습니다.

## 검증
- `python3 -m unittest -v tests.test_smoke`
  - 통과 (`Ran 94 tests`, `OK`)
- `python3 -m unittest -v tests.test_web_app.WebAppServiceTest.test_handle_chat_entity_web_search_serializes_claim_coverage`
  - 통과 (`Ran 1 test`, `OK`)
- `git diff --check -- core/agent_loop.py tests/test_smoke.py tests/test_web_app.py README.md docs/PRODUCT_SPEC.md docs/ACCEPTANCE_CRITERIA.md`
  - 통과 (출력 없음)
- 수동 truth 대조
  - `work/3/31/2026-03-31-entity-card-zero-strong-slot-badge-downgrade.md`
  - `verify/3/31/2026-03-31-dual-probe-history-card-reload-exact-field-retention-verification.md`
  - `.pipeline/codex_feedback.md`
  - `core/agent_loop.py`
  - `tests/test_smoke.py`
  - `README.md`
  - `docs/PRODUCT_SPEC.md`
  - `docs/ACCEPTANCE_CRITERIA.md`
- 이번 라운드에서 재실행하지 않은 검증
  - `python3 -m unittest -v tests.test_web_app`
  - `make e2e-test`
  - 이유: 이번 변경은 entity-card verification label semantic 1건과 그 docs sync가 전부였고, latest `/work`도 full `tests.test_web_app`나 browser contract 변경을 주장하지 않았으므로 `tests.test_smoke`, focused `tests.test_web_app` 1건, scoped diff check만으로 직접 영향 범위를 재검수할 수 있었습니다.

## 남은 리스크
- 이번 라운드는 initial entity-card response와 docs truth를 잠갔지만, current user-visible history-card header가 zero-strong-slot entity-card에서 downgraded verification label을 exact하게 직렬화하는지는 `tests.test_web_app`에 아직 explicit regression이 없습니다.
- 따라서 다음 smallest same-family current-risk slice는 `session.web_search_history` entity-card summary에서 zero-strong-slot downgrade label과 source-role exact field를 잠그는 test-only slice 1건입니다.
- dirty worktree가 여전히 넓어 다음 검수도 unrelated 변경을 끌어오지 않도록 scoped verification discipline이 계속 필요합니다.
