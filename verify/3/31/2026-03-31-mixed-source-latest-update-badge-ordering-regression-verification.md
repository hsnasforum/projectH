## 변경 파일
- `.pipeline/codex_feedback.md`
- `verify/3/31/2026-03-31-mixed-source-latest-update-badge-ordering-regression-verification.md`

## 사용 skill
- `round-handoff`

## 변경 이유
- 사용자 요청에 따라 `AGENTS.md`, `work/README.md`, `verify/README.md`, `.pipeline/README.md`를 먼저 읽고, 최신 Claude `/work`인 `work/3/31/2026-03-31-mixed-source-latest-update-badge-ordering-regression.md`와 같은 날짜 최신 `/verify`인 `verify/3/31/2026-03-31-web-search-history-exact-badge-integration-verification.md`를 기준으로 이번 라운드 주장만 다시 검수해야 했습니다.
- latest `/work`는 mixed-source `latest_update` history badge ordering regression 1개와, 그 테스트가 드러낸 `live` profile source-selection threshold 완화 1건만 주장하므로, 이번 검수도 해당 테스트/로직/직렬화 경로와 current MVP 범위 일탈 여부만 좁게 다시 확인하면 충분했습니다.

## 핵심 변경
- 판정: latest `/work`의 주장은 현재 코드와 일치합니다.
- `tests/test_web_app.py`에는 `test_handle_chat_mixed_source_latest_update_badge_ordering`가 실제로 추가되어 있고, `handle_chat() -> session.web_search_history[0]`에서 아래 exact field를 직접 검증합니다.
  - `answer_mode == "latest_update"`
  - `verification_label == "공식+기사 교차 확인"`
  - `source_roles == ["보조 기사", "공식 기반"]`
- `core/agent_loop.py`의 `_select_ranked_web_sources()`에서는 `live` profile threshold가 실제로 `top_score - 9`에서 `top_score - 12`로 바뀌어 있습니다.
- one-off 재현 스크립트로 같은 fixture를 직접 다시 돌린 결과, source ranking truth는 다음과 같았습니다.
  - ranked score: news 기사 38점, official 도메인 28점
  - 현재 threshold(`-12`)에서는 두 source가 모두 선택되어 `공식+기사 교차 확인`과 `["보조 기사", "공식 기반"]`가 나옵니다.
  - 이전 threshold(`-9`)를 그대로 적용하면 news 기사만 남아 label이 `단일 출처 참고`로 내려갑니다.
- 따라서 이번 라운드는 이전 `.pipeline/codex_feedback.md`가 적어 둔 `["공식 기반", "보조 기사"]` 기대값을 임의로 바꾼 것이 아니라, 실제 score-rank ordering truth를 반영하면서 minimal production fix를 추가한 것으로 확인했습니다.
- 범위도 현재 projectH 방향에서 벗어나지 않았습니다.
  - secondary-mode web investigation hardening 범위 안입니다.
  - docs, browser markup, approval flow, reviewed-memory, broader web-search-first widening은 이번 라운드에서 확인되지 않았습니다.
  - dirty worktree는 넓지만 latest `/work`가 주장한 변경 범위와 직접 충돌하는 흔적은 이번 검수에서 보이지 않았습니다.

## 검증
- `python3 -m unittest -v tests.test_web_app`
  - 통과 (`Ran 101 tests in 1.568s`, `OK`)
- `git diff --check -- tests/test_web_app.py app/web.py storage/web_search_store.py core/agent_loop.py`
  - 통과 (출력 없음)
- `git diff --check`
  - 통과 (출력 없음)
- one-off `python3` 재현 스크립트
  - same fixture로 `AgentLoop._rank_web_search_sources()`와 `_select_ranked_web_sources()`를 직접 확인해 old/new threshold 차이를 재현했습니다.
  - 결과: `selected_now`는 news+official 2건, `selected_old`는 news 1건만 남았고, `label_old`는 실제로 `단일 출처 참고`였습니다.
- one-off `python3` reload 재현 스크립트
  - 같은 mixed-source fixture로 `handle_chat()`를 두 번 호출해, initial history와 `방금 검색한 결과 다시 보여줘` reload 응답 모두에서 `공식+기사 교차 확인`과 `["보조 기사", "공식 기반"]`가 유지되는 것도 확인했습니다.
- 수동 truth 대조
  - `work/3/31/2026-03-31-mixed-source-latest-update-badge-ordering-regression.md`
  - `verify/3/31/2026-03-31-web-search-history-exact-badge-integration-verification.md`
  - `tests/test_web_app.py`
  - `core/agent_loop.py`
  - `app/web.py`
  - `docs/NEXT_STEPS.md`
  - `docs/MILESTONES.md`
  - `docs/TASK_BACKLOG.md`
- 이번 라운드에서 재실행하지 않은 검증
  - `make e2e-test`
  - 이유: latest `/work`가 browser-visible markup/CSS나 docs를 바꾸지 않았고, 이번 변경은 `handle_chat -> web_search_history`와 web source selection 로직에만 국한되어 있어 `tests.test_web_app`와 scoped diff check면 충분했습니다.

## 남은 리스크
- mixed-source latest-update의 reload show-only 경로는 현재 manual repro로는 맞지만, dedicated regression이 아직 없습니다. 다음 좁은 슬라이스로 reload exact-field 보호를 추가하는 편이 안전합니다.
- `live` threshold 완화로 상대적으로 낮은 점수의 source가 포함될 가능성은 조금 늘었지만, ranking 우선순위와 `max_items` 제한은 그대로 유지됩니다.
- dirty worktree가 넓어 다음 라운드도 unrelated 변경을 건드리지 않는 focused slice가 안전합니다.
