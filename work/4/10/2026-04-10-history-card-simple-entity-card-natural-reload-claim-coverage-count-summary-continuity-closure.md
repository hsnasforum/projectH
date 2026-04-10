# history-card simple entity-card natural-reload claim-coverage count-summary continuity closure

## 변경 파일
- `tests/test_web_app.py` — 기존 `test_handle_chat_actual_entity_search_natural_reload_exact_fields` 시나리오 패턴을 mirror 해, 자연어 reload → 첫 follow-up → 두 번째 follow-up 까지 `session.web_search_history[0].claim_coverage_summary` dict 가 baseline 과 동일하게 유지되는지 각 단계에서 잠그는 focused 서비스 회귀 `test_handle_chat_actual_entity_search_natural_reload_second_follow_up_preserves_claim_coverage_count_summary` 추가
- `e2e/tests/web-smoke.spec.mjs` — 신규 시나리오 `history-card entity-card 자연어 reload 후 두 번째 follow-up 질문에서 WEB badge, 설명 카드, 설명형 단일 출처, 백과 기반이 drift하지 않습니다` 추가. simple single-source entity-card seed 를 재사용해 click-reload → 자연어 reload (`"방금 검색한 결과 다시 보여줘"`) → 첫 follow-up → 두 번째 follow-up 흐름을 실행하고, 각 단계에서 history-card `.meta` 가 `사실 검증 단일 출처 1 · 단일 출처 상태 1건.` 정확 문자열과 합성 순서/separator 조건을 유지하는지 잠금

## 사용 skill
- `round-handoff`
- `e2e-smoke-triage`

## 변경 이유
- 직전 `/work` (`2026-04-10-history-card-entity-card-reload-second-follow-up-claim-coverage-count-summary-continuity-tightening.md`) 와 그 `/verify` 는 simple entity-card **click-reload** 가족의 show-only reload → first follow-up → second follow-up 경로에서 `claim_coverage_summary` continuity 를 잠갔음
- 같은 simple single-source entity-card 계열 내부의 아직 잠기지 않은 current-risk 는 **자연어 reload** (`"방금 검색한 결과 다시 보여줘"`) 가족. 기존 `test_handle_chat_actual_entity_search_natural_reload_exact_fields` 는 자연어 reload 단계의 `response_origin` exact fields 만 잠갔고, 해당 경로가 첫/두 번째 follow-up 까지 이어졌을 때 `session.web_search_history` 의 `claim_coverage_summary` dict 가 드리프트하지 않는지에 대한 명시적 회귀가 없었음
- 브라우저 쪽에서도 natural-reload follow-up 커버리지는 zero-strong / actual-search / dual-probe / noisy 가족에만 존재했고, simple single-source 가족의 count-summary `.meta` 지속성은 스모크에 없었음
- 이 슬라이스는 런타임 변경 없이 기존 natural-reload 회귀/시나리오 패턴을 mirror 해 하나의 focused 서비스 회귀와 하나의 focused 브라우저 시나리오로 자연어 reload 가족의 count-summary gap 을 닫는 범위임. latest-update / general / actual-search / dual-probe / zero-strong / noisy / stored-origin-missing fallback 은 의도적으로 범위 밖

## 핵심 변경
1. **`tests/test_web_app.py` focused 서비스 회귀 추가**
   - `test_handle_chat_actual_entity_search_natural_reload_second_follow_up_preserves_claim_coverage_count_summary`
     - 첫 `handle_chat({user_text})` 호출 → baseline `claim_coverage_summary` dict 추출 (strong+weak+missing > 0 보장)
     - `handle_chat({user_text: "방금 검색한 결과 다시 보여줘"})` 자연어 reload 호출
     - `handle_chat({user_text + load_web_search_record_id})` 첫 follow-up 호출
     - `handle_chat({user_text + load_web_search_record_id})` 두 번째 follow-up 호출
     - 내부 헬퍼 `_assert_same_counts(result, stage)` 로 각 단계에서: `ok`, `actions_taken` 에 `load_web_search_record` 포함, `session.web_search_history` 에 동일 record_id 항목 존재, `claim_coverage_summary == baseline_counts` 를 잠금
   - 기존 `test_handle_chat_actual_entity_search_natural_reload_exact_fields` 와 동일한 `_FakeWebSearchTool`/`AppSettings`/`WebAppService` fixture 를 그대로 재사용했고 신규 helper/import/fixture 파일은 추가하지 않음. 두 follow-up 은 서로 다른 `user_text` (`"이 검색 결과 요약해줘"` / `"장르만 한 줄로 다시 정리해줘"`) 를 사용해 실제로 두 번의 turn 이 발생하는지 확인함
2. **`e2e/tests/web-smoke.spec.mjs` 신규 브라우저 시나리오 추가**
   - 시나리오 이름: `history-card entity-card 자연어 reload 후 두 번째 follow-up 질문에서 WEB badge, 설명 카드, 설명형 단일 출처, 백과 기반이 drift하지 않습니다`
   - 기존 first/second click-reload follow-up 시나리오의 seed (`response_origin` 에 `provider/badge/label/answer_mode/verification_label/source_roles`, `claim_coverage: [{weak}]`, `claim_coverage_progress_summary: "단일 출처 상태 1건."`) 모양을 그대로 재사용
   - 흐름:
     - `renderSearchHistory` (with client-seeded `claim_coverage_summary: {strong:0, weak:1, missing:0}` 과 `claim_coverage_progress_summary: "단일 출처 상태 1건."`) → `다시 불러오기` 클릭 (record 를 server 세션에 등록하기 위한 step)
     - `sendRequest({ user_text: "방금 검색한 결과 다시 보여줘" })` 자연어 reload
     - `sendRequest({ user_text: "이 검색 결과 요약해줘", load_web_search_record_id })` 첫 follow-up
     - `sendRequest({ user_text: "장르만 한 줄로 다시 정리해줘", load_web_search_record_id })` 두 번째 follow-up
   - 각 단계에서:
     - `#response-origin-badge === "WEB"`, `#response-answer-mode-badge === "설명 카드"`
     - 두 번째 follow-up 이후 `#response-origin-badge` 의 `web` class 와 `#response-origin-detail` 가 `설명형 단일 출처`, `백과 기반` 을 포함하는지 확인
     - 자연어 reload 직후와 두 번째 follow-up 직후 모두 history-card `.meta` 가 `"사실 검증 단일 출처 1 · 단일 출처 상태 1건."` 정확 문자열, leading/trailing separator artifact 없음, count 라인이 progress 라인보다 앞에 오는 합성 순서 (`indexOf` 비교), 그리고 answer-mode label (`설명 카드` / `최신 확인` / `일반 검색`) 누출 없음 을 잠금
   - 기존 selector (`#search-history-box`, `.history-item`, `.meta`, `#response-origin-badge`, `#response-answer-mode-badge`, `#response-origin-detail`) 와 `prepareSession`, `renderSearchHistory`, `sendRequest`, `fs/path` 헬퍼만 재사용했고 새 helper/selector/fixture 파일을 만들지 않음

## 검증
이번 라운드 실행:
- `python3 -m unittest -v tests.test_web_app.WebAppServiceTest.test_handle_chat_actual_entity_search_natural_reload_exact_fields` → `ok`
- `python3 -m unittest -v tests.test_web_app.WebAppServiceTest.test_handle_chat_actual_entity_search_natural_reload_second_follow_up_preserves_claim_coverage_count_summary` → `ok`
- `cd e2e && npx playwright test tests/web-smoke.spec.mjs -g "history-card entity-card 자연어 reload 후 두 번째 follow-up 질문에서 WEB badge, 설명 카드, 설명형 단일 출처, 백과 기반이 drift하지 않습니다" --reporter=line` → `1 passed (6.7s)`
- `git diff --check -- tests/test_web_app.py e2e/tests/web-smoke.spec.mjs work/4/10` → 출력 없음 (공백 오류 없음)

이번 라운드에서 재실행하지 않음:
- `python3 -m unittest -v tests.test_web_app` 전체 슈트 — 본 슬라이스는 기존 `handle_chat` 경로에 순수 추가 회귀만 붙였고 기존 로직 변경이 없음. handoff 도 focused 두 회귀만 재실행을 요구함
- broader Playwright suite 또는 `make e2e-test` — browser-visible contract 가 넓어지지 않았고 단일 신규 isolated scenario 하나만 추가함
- 다른 click-reload first/second follow-up 시나리오나 zero-strong / actual-search / dual-probe / noisy / latest-update / general natural-reload 시나리오 — 이번 슬라이스는 simple single-source entity-card natural-reload only 로 의도적으로 한정

## 남은 리스크
- 브라우저 `.meta` 잠금은 `formatClaimCoverageCountSummary({weak:1})` 이 `"단일 출처 1"` 을 내고 `detailLines.join(" · ")` separator 가 ` · ` 라는 점에 의존함. 포맷(`app/static/app.js:2225-2232`) 이 바뀌면 이 스모크가 먼저 깨짐 — 다만 같은 문자열이 다른 claim-coverage UI 곳에서도 사용 중이므로 drift 범위는 런타임 전반과 동일
- 서비스 회귀의 `baseline_counts` 는 첫 호출의 실제 mock entity-card 결과를 그대로 사용함. `_FakeWebSearchTool` 기본 응답이나 `_summarize_claim_coverage` 분류 기준이 바뀌어 slot 수가 0 이 되면 `assertGreater(..., 0)` 에서 먼저 실패해 원인을 빠르게 가리킴 — 의도된 failure-first 설계
- 내부 헬퍼 `_assert_same_counts` 의 `result` 인자에는 `Any` 타입 힌트를 의도적으로 사용하지 않음 (`from typing import Any` 가 해당 파일 상단에 import 되어 있지 않음). Dict-like 구조를 전제로 한 assertion 시퀀스만 수행하며, 타입 오류가 생기면 각 assertion 이 우선 실패해 원인을 빠르게 가리킴
- 자연어 reload 와 click-reload 두 경로는 `core/agent_loop.py` 에서 show-only 여부가 다르지만 (`show_only` prefix 감지), 두 경로 모두 `session.web_search_history` 를 `list_session_record_summaries` 로 재직렬화하므로 `claim_coverage_summary` 는 동일한 source 에서 파생됨. 따라서 이 슬라이스는 두 경로가 공통으로 의존하는 store→serializer 경로의 회귀를 natural-reload 맥락에서도 잠그는 효과가 있음
- latest-update / general / actual-search / dual-probe / zero-strong / noisy / stored-origin-missing fallback 가족의 natural-reload follow-up 경로는 이 슬라이스 범위 밖이며 각각 다른 `_infer_reloaded_answer_mode` 분기와 source-role 필터링을 함께 고려해야 하므로 별도 라운드로 남겨둠
- client-seeded `claim_coverage_summary` 값이 record 의 실제 `_summarize_claim_coverage` 결과와 일치해야 pre/post `.meta` 가 동일 문자열을 유지함. 시드가 비대칭이면 follow-up 이후 서버 재직렬화에서 서로 다른 값이 나와 `.meta` 가 튈 수 있어, 이번 라운드는 두 값을 동일하게 맞춰 잠갔음
