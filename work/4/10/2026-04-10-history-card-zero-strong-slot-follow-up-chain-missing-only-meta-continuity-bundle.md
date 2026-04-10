# history-card zero-strong-slot follow-up-chain missing-only meta continuity bundle

## 변경 파일
- `tests/test_web_app.py` — zero-strong-slot entity-card 의 click-reload 와 natural-reload 두 체인 모두에서 baseline history entry 가 downgraded `verification_label`, missing-only `claim_coverage_summary` (`strong==0`, `weak==0`, `missing>0`), 빈 `claim_coverage_progress_summary` 를 유지하는지 각 단계 (`초기 검색 → reload → 첫 follow-up → 두 번째 follow-up`) 에서 잠그는 두 개의 focused 서비스 회귀 추가:
  - `test_handle_chat_zero_strong_slot_entity_card_history_card_reload_second_follow_up_preserves_missing_only_count_summary` (click-reload chain)
  - `test_handle_chat_zero_strong_slot_entity_card_natural_reload_second_follow_up_preserves_missing_only_count_summary` (natural-reload chain)
- `e2e/tests/web-smoke.spec.mjs` — zero-strong-slot click-reload 와 natural-reload 두 체인에 대해 missing-only `.meta` continuity 를 잠그는 두 개의 신규 브라우저 시나리오 추가:
  - `entity-card zero-strong-slot 다시 불러오기 후 두 번째 follow-up 질문에서 missing-only count-summary meta가 truthfully 유지됩니다`
  - `entity-card zero-strong-slot 자연어 reload 후 두 번째 follow-up에서 missing-only count-summary meta가 truthfully 유지됩니다`

## 사용 skill
- `round-handoff`
- `e2e-smoke-triage`

## 변경 이유
- 직전 `/work` (`2026-04-10-history-card-zero-strong-slot-missing-only-count-summary-meta-truth-sync.md`) 와 그 `/verify` 는 zero-strong missing-only count-summary `.meta` 경로의 **show-only click-reload 단일 분기** 만 잠갔음. 같은 가족 내부에 다음 분기가 여전히 열려 있었음:
  - click-reload 이후 `user_text + load_web_search_record_id` 첫/두 번째 follow-up
  - 자연어 reload (`"방금 검색한 결과 다시 보여줘"`) 이후 첫/두 번째 follow-up
- 기존 `tests/test_web_app.py:16545-16845` 의 연속성 테스트 대부분은 `response_origin` / `source_paths` continuity 만 잠갔고, missing-only `claim_coverage_summary` 가 reload-follow-up chain 을 통과해 유지되는지를 명시적으로 잠그지 않음
- `e2e/tests/web-smoke.spec.mjs` 의 기존 click-reload / natural-reload 두 번째 follow-up 시나리오는 `claim_coverage: []`, `claim_coverage_summary` 미시드 상태로 empty-claim-coverage 분기만 exercise 해서 실제 런타임의 missing-only 분기를 관찰하지 못함
- `app/static/app.js:2225-2231` + `:2958-2969` 의 렌더러 분기에 의해 `formatClaimCoverageCountSummary({missing:N})` 는 `"미확인 N"` 단일 segment 를 내고, investigation 카드는 answer-mode label 을 skip 하므로 `.meta` 는 `"사실 검증 미확인 N"` 한 줄로 구성됨. reload-follow-up chain 전체에서 이 한 줄이 유지되는지가 남은 user-visible risk 였음
- handoff 지시대로 네 개 시나리오 micro-loop 대신 하나의 bounded bundle 로 click-reload 와 natural-reload 두 체인을 같은 라운드에 닫음. latest-update / general / noisy / docs / pipeline 은 의도적으로 범위 밖

## 핵심 변경
1. **`tests/test_web_app.py` focused 서비스 회귀 두 건 추가**
   - 두 회귀 모두 기존 `_FakeWebSearchTool` 구성(두 개의 namu.wiki/ko.wikipedia.org 결과) 을 그대로 재사용해 zero-strong-slot entity-card baseline 을 만듦
   - 공통 내부 헬퍼 `_assert_missing_only_meta_continuity(result, stage)` 로 각 단계에서 다음을 잠금:
     - `result["ok"]` 참
     - `actions_taken` 에 `load_web_search_record` 포함
     - `session.web_search_history` 에 동일 `record_id` 항목 존재
     - `verification_label` 이 baseline 과 동일
     - `claim_coverage_summary.strong == 0`, `.weak == 0`
     - `claim_coverage_summary.missing` 이 baseline `missing` 값과 정확히 동일
     - `claim_coverage_progress_summary == ""`
   - click-reload 회귀: 초기 검색 → `{load_web_search_record_id}` show-only reload → `{user_text + load_web_search_record_id}` 첫 follow-up → `{user_text + load_web_search_record_id}` 두 번째 follow-up 네 단계
   - natural-reload 회귀: 초기 검색 → `{user_text: "방금 검색한 결과 다시 보여줘"}` 자연어 reload → 첫 follow-up → 두 번째 follow-up 네 단계
   - baseline `missing` 값을 그대로 기록해 `_FakeWebSearchTool` 내부 분류 세부가 바뀌어도 `missing > 0` 이면 failure-first 로 동작하며, 각 단계 사이 drift 만 엄격히 비교함
2. **`e2e/tests/web-smoke.spec.mjs` 신규 브라우저 시나리오 두 건 추가**
   - 두 시나리오 모두:
     - 디스크 record 의 `claim_coverage` 에 다섯 개 `{slot, status:"missing", status_label:"미확인"}` 항목을 시드 (기존 `[]` 와 다름)
     - `renderSearchHistory` item 에 `claim_coverage_summary: {strong:0, weak:0, missing:5}` 와 `claim_coverage_progress_summary: ""` 를 시드 (기존 스모크와 다름) — 서버 `_summarize_claim_coverage` 가 재직렬화할 때 client seed 와 동일한 결과가 나오도록 정렬
   - 공통 어서션 (각 단계마다):
     - `.meta` 정확 문자열 `"사실 검증 미확인 5"`
     - `not.toContainText("·")` — single-category count segment 이므로 separator 가 전혀 등장해서는 안 됨
     - `not.toContainText("설명 카드")` / `"최신 확인"` / `"일반 검색"` — investigation 이므로 answer-mode label 이 skip 되어야 함
     - leading/trailing `·` separator artifact 부정
     - `#response-origin-badge === "WEB"` + `web` class, `#response-answer-mode-badge === "설명 카드"`, `#response-origin-detail` 이 `설명형 단일 출처` / `백과 기반` 포함, `#context-box` 가 `namu.wiki` / `ko.wikipedia.org` 포함
   - click-reload 시나리오 흐름: `renderSearchHistory` → `다시 불러오기` 클릭 → 첫 follow-up → `.meta` 어서션 → 두 번째 follow-up → `.meta` 어서션
   - natural-reload 시나리오 흐름: `renderSearchHistory` → `다시 불러오기` 클릭 → `sendRequest({ user_text: "방금 검색한 결과 다시 보여줘" })` → 첫 follow-up → `.meta` 어서션 → 두 번째 follow-up → `.meta` 어서션
   - 기존 selector (`#search-history-box`, `.history-item`, `.meta`, `#response-origin-badge`, `#response-answer-mode-badge`, `#response-origin-detail`, `#context-box`) 와 `prepareSession`, `renderSearchHistory`, `sendRequest`, `fs/path` 헬퍼만 재사용했고 새 helper/selector/fixture 파일을 만들지 않음
   - 기존 empty-summary 스모크(`[]` claim_coverage + 빈 progress) 시나리오는 전혀 건드리지 않음 (handoff 지시)

## 검증
이번 라운드 실행:
- `python3 -m unittest -v tests.test_web_app.WebAppServiceTest.test_handle_chat_zero_strong_slot_entity_card_history_card_reload_second_follow_up_preserves_missing_only_count_summary` → `ok`
- `python3 -m unittest -v tests.test_web_app.WebAppServiceTest.test_handle_chat_zero_strong_slot_entity_card_natural_reload_second_follow_up_preserves_missing_only_count_summary` → `ok`
- `cd e2e && npx playwright test tests/web-smoke.spec.mjs -g "entity-card zero-strong-slot 다시 불러오기 후 두 번째 follow-up 질문에서 missing-only count-summary meta가 truthfully 유지됩니다" --reporter=line` → `1 passed (16.2s)`
- `cd e2e && npx playwright test tests/web-smoke.spec.mjs -g "entity-card zero-strong-slot 자연어 reload 후 두 번째 follow-up에서 missing-only count-summary meta가 truthfully 유지됩니다" --reporter=line` → `1 passed (13.1s)`
- `git diff --check -- tests/test_web_app.py e2e/tests/web-smoke.spec.mjs work/4/10` → 출력 없음 (공백 오류 없음)

이번 라운드에서 재실행하지 않음:
- `python3 -m unittest -v tests.test_web_app` 전체 슈트 — 본 슬라이스는 기존 `handle_chat` 경로에 순수 추가 회귀만 붙였고 기존 로직 변경이 없음. handoff 도 focused 두 회귀만 재실행을 요구함
- broader Playwright suite 또는 `make e2e-test` — browser-visible contract 가 넓어지지 않았고 두 개의 신규 isolated scenario 만 추가함
- 기존 empty-summary / 다른 가족(latest-update, general, noisy, actual-search, dual-probe) 시나리오 — handoff 는 이들을 그대로 두도록 명시함

## 남은 리스크
- 두 브라우저 시나리오의 `.meta` 어서션은 시드된 디스크 record 의 `missing` slot 개수(5) 에 의존함. 시드 배열을 수정하면 서버가 재직렬화하는 `missing` 카운트도 함께 바뀌므로 `toHaveText("사실 검증 미확인 5")` 를 같이 조정해야 함 — 이 의존성은 시드 배열 길이와 단일 지점에서 관리되므로 실수 여지가 제한적
- 두 서비스 회귀는 `missing > 0` 과 baseline drift 부재만 단언함. 실제 런타임이 empty-claim-coverage 경로로 드리프트하면 `assertGreater(..., 0)` 에서 먼저 실패해 원인을 빠르게 가리킴 — 의도된 failure-first 설계
- 내부 헬퍼 `_assert_missing_only_meta_continuity` 의 `result` 인자는 `Any` 타입 힌트를 의도적으로 사용하지 않음 (`from typing import Any` 가 해당 파일 상단에 import 되어 있지 않음). dict-like 구조를 전제로 한 assertion 시퀀스만 수행하며, 타입 오류가 생기면 각 assertion 이 우선 실패함
- `formatClaimCoverageCountSummary({missing:N})` 이 `"미확인 N"` 을 내고 `detailLines.join(" · ")` separator 가 ` · ` 라는 포맷 가정(`app/static/app.js:2225-2232`, `:2969`)에 의존함. 포맷이 바뀌면 두 스모크가 먼저 깨짐 — 같은 문자열이 다른 claim-coverage UI 곳에서도 사용 중이므로 drift 범위는 런타임 전반과 동일
- 두 follow-up 의 `user_text` 는 서로 다른 문자열(`"이 검색 결과 요약해줘"` / `"이 게임 장르만 한 줄로 다시 정리해줘"`) 을 사용함. 향후 `handle_chat` 이 특정 문자열을 다른 intent 로 해석해 reload-follow-up path 가 아닌 다른 경로로 빠지면 회귀의 `actions_taken` 단언에서 먼저 실패해 원인을 빠르게 가리킴
- latest-update / general / noisy / actual-search / dual-probe 가족의 missing-only 또는 mixed `.meta` continuity 는 이번 슬라이스 범위 밖이며, 각각 다른 `_infer_reloaded_answer_mode` 분기와 source-role 필터링을 고려해야 하므로 별도 라운드로 남겨둠
- 기존 empty-summary negative 스모크는 `claim_coverage: []` 에서 `.meta` 가 생성되지 않는 edge case 를 지키는 보조 회귀로 유지함. 본 슬라이스는 그것과 별개의 `.meta` 존재 분기를 잠금
