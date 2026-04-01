## 변경 파일
- `.pipeline/codex_feedback.md`
- `verify/3/31/2026-03-31-load-web-search-record-id-entity-card-exact-field-regression-verification.md`

## 사용 skill
- `round-handoff`

## 변경 이유
- 사용자 요청에 따라 `AGENTS.md`, `work/README.md`, `verify/README.md`, `.pipeline/README.md`를 먼저 읽고, 최신 Claude `/work`인 `work/3/31/2026-03-31-load-web-search-record-id-entity-card-exact-field-regression.md`와 같은 날짜 최신 `/verify`인 `verify/3/31/2026-03-31-load-web-search-record-id-mixed-source-latest-update-exact-field-regression-verification.md`를 기준으로 이번 라운드 주장만 다시 검수해야 했습니다.
- latest `/work`는 `tests/test_web_app.py`에 entity-card `load_web_search_record_id` exact-field regression 1개를 추가했고 production 코드와 문서는 바꾸지 않았다고 주장하므로, 이번 검수도 해당 테스트 존재 여부, 범위 이탈 여부, 필요한 재검증만 다시 돌리면 충분했습니다.

## 핵심 변경
- 판정: latest `/work`의 주장은 현재 코드와 일치합니다.
- `tests/test_web_app.py`에는 `test_handle_chat_load_web_search_record_id_entity_card_exact_fields`가 실제로 존재하며, same-session history-card 선택 경로에서 아래 exact field를 직접 고정합니다.
  - `second["response"]["actions_taken"] == ["load_web_search_record"]`
  - `second["response"]["web_search_record_path"] == first["response"]["web_search_record_path"]`
  - `second["response"]["response_origin"]["answer_mode"] == "entity_card"`
  - `second["response"]["response_origin"]["verification_label"] == "설명형 단일 출처"`
  - `second["response"]["response_origin"]["source_roles"] == ["백과 기반"]`
- current worktree 기준 scoped 파일 수정 시각도 `production 코드 변경 없음` 주장과 맞습니다.
  - `tests/test_web_app.py`: `2026-03-31 16:07:32 +0900`
  - `core/agent_loop.py`: `2026-03-31 15:31:40 +0900`
  - `app/web.py`: `2026-03-31 10:13:02 +0900`
  - `storage/web_search_store.py`: `2026-03-26 21:03:54 +0900`
  - latest `/work` closeout 시각은 `2026-03-31 16:08:04 +0900`이므로, 이번 검수 범위에서는 테스트 파일만 직전 검증 이후 새로 갱신된 것으로 확인했습니다.
- 범위도 현재 projectH 방향에서 벗어나지 않았습니다.
  - shipped secondary-mode web investigation의 history-card reload contract을 보호하는 test-only slice입니다.
  - approval flow, reviewed-memory, broader product 방향, UI/문서 widening은 이번 라운드에서 확인되지 않았습니다.
  - whole-project audit이 필요한 징후는 이번 라운드 범위에서는 보이지 않아 `report/`는 만들지 않았습니다.
- current worktree 기준으로 `load_web_search_record_id` direct-selection exact-field regression family는 이제 current shipped 주요 answer-mode 변형을 모두 덮습니다.
  - single-source latest_update
  - mixed-source latest_update
  - entity_card

## 검증
- `python3 -m unittest -v tests.test_web_app`
  - 통과 (`Ran 106 tests in 1.664s`, `OK`)
- `git diff --check -- tests/test_web_app.py app/web.py storage/web_search_store.py core/agent_loop.py`
  - 통과 (출력 없음)
- 수동 truth 대조
  - `work/3/31/2026-03-31-load-web-search-record-id-entity-card-exact-field-regression.md`
  - `verify/3/31/2026-03-31-load-web-search-record-id-mixed-source-latest-update-exact-field-regression-verification.md`
  - `tests/test_web_app.py`
  - `docs/NEXT_STEPS.md`
  - `docs/MILESTONES.md`
  - `docs/TASK_BACKLOG.md`
- 이번 라운드에서 재실행하지 않은 검증
  - `make e2e-test`
  - 이유: latest `/work`가 browser-visible markup이나 production 경로가 아닌 test-only slice이고, 현재 라운드 주장은 exact-field regression 1건뿐이라 `tests.test_web_app`와 scoped diff check면 충분했습니다.

## 남은 리스크
- `tests/test_web_app.py` 자체는 같은 날 여러 라운드가 누적된 dirty 상태라 whole-file diff만으로 이번 라운드를 분리하기 어렵습니다. 이번 검수는 latest `/work`, 직전 `/verify`, scoped 파일 수정 시각, exact test 함수 존재를 함께 대조해 좁혔습니다.
- `_build_user_text`가 `load_web_search_record_id`만 있을 때 show-only 경로를 타게 만드는 암묵적 의존은 이번 entity-card 테스트에서도 그대로 남아 있습니다.
- unit-level direct-selection exact-field family는 현재 answer-mode 기준으로 닫혔지만, 그 다음 슬라이스를 무엇으로 잡을지는 현재 MVP 우선순위 판단이 더 필요합니다.
  - browser-visible history-card click smoke를 열지
  - secondary-mode investigation hardening의 다른 user-visible risk reduction을 고를지
- dirty worktree가 넓어 unrelated 변경을 섞지 않는 운영 판단이 계속 필요합니다.
