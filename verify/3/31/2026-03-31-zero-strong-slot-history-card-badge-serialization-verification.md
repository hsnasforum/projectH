# 2026-03-31 zero-strong-slot history-card badge serialization verification

## 변경 파일
- `verify/3/31/2026-03-31-zero-strong-slot-history-card-badge-serialization-verification.md`
- `.pipeline/codex_feedback.md`

## 사용 skill
- `round-handoff`
- `investigation-quality-audit`

## 변경 이유
- 사용자 요청에 따라 `AGENTS.md`, `work/README.md`, `verify/README.md`, `.pipeline/README.md`를 먼저 다시 읽고, latest Claude `/work`인 `work/3/31/2026-03-31-zero-strong-slot-history-card-badge-serialization.md`와 latest same-day `/verify`인 `verify/3/31/2026-03-31-entity-card-zero-strong-slot-badge-downgrade-verification.md`를 기준으로 이번 라운드 주장만 좁게 검수해야 했습니다.
- latest `/work`는 zero-strong-slot entity-card의 history-card header 직렬화 truth를 `tests/test_web_app.py` 한 건으로 잠그는 test-only slice라고 적고 있으므로, 이번 검수에서는 해당 regression 존재 여부, production/docs 무변경 주장, 현재 MVP 방향 일탈 여부, 그리고 note가 적은 최소 검증만 다시 확인하면 충분했습니다.

## 핵심 변경
- 판정: latest `/work`의 test-only 변경 주장은 현재 코드와 일치합니다.
- `tests/test_web_app.py`에는 `test_handle_chat_zero_strong_slot_entity_card_history_badge_serialization`가 실제로 추가되어 있고, 저장된 `session.web_search_history[0]`에서 `answer_mode == "entity_card"`, downgraded `verification_label`, non-empty label, non-empty `source_roles`를 검증합니다.
- 이번 라운드의 production 추가 변경은 없습니다. `core/agent_loop.py`에는 직전 zero-strong-slot badge downgrade round의 로직만 남아 있고, latest `/work`가 주장한 이번 round의 수정 범위는 `tests/test_web_app.py` 한 파일뿐입니다.
- docs 추가 변경도 없습니다. 이번 slice는 current shipped history-card summary serialization regression 1건을 잠그는 test-only follow-up이라, `README.md`, `docs/PRODUCT_SPEC.md`, `docs/ACCEPTANCE_CRITERIA.md`를 다시 넓힐 이유는 없었습니다.
- 범위도 현재 projectH 방향에서 벗어나지 않습니다. 이 라운드는 strong/weak/unresolved slot clarity 축 안에서 방금 landed한 zero-strong-slot badge semantics를 history-card header까지 맞추는 same-family current-risk reduction 1건입니다.
- whole-project audit이 필요한 징후는 아니므로 `report/`는 만들지 않았습니다.

## 검증
- `python3 -m unittest -v tests.test_web_app`
  - 통과 (`Ran 117 tests`, `OK`)
- `git diff --check -- core/agent_loop.py tests/test_web_app.py`
  - 통과 (출력 없음)
- 수동 truth 대조
  - `work/3/31/2026-03-31-zero-strong-slot-history-card-badge-serialization.md`
  - `verify/3/31/2026-03-31-entity-card-zero-strong-slot-badge-downgrade-verification.md`
  - `.pipeline/codex_feedback.md`
  - `tests/test_web_app.py`
  - `core/agent_loop.py`
- 이번 라운드에서 재실행하지 않은 검증
  - `python3 -m unittest -v tests.test_smoke`
  - `make e2e-test`
  - 이유: 이번 변경은 `tests.test_web_app`의 history-card serialization regression 1건만 추가한 test-only slice였고, browser-visible 새 동작이나 production hunk가 없어서 full smoke/e2e까지 다시 돌릴 필요는 없었습니다.

## 남은 리스크
- zero-strong-slot entity-card의 initial response와 history-card summary serialization은 잠겼지만, stored record를 `load_web_search_record_id`로 다시 여는 history-card reload 경로에서 downgraded `verification_label`과 related exact field가 유지되는지는 아직 explicit regression이 없습니다.
- 따라서 다음 smallest same-family current-risk slice는 zero-strong-slot entity-card의 history-card reload exact-field retention을 `tests/test_web_app.py` 1건으로 잠그는 것입니다.
- dirty worktree가 넓으므로 다음 검수도 unrelated 파일을 끌어오지 않는 scoped verification discipline이 계속 필요합니다.
