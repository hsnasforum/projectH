# history-card zero-strong-slot missing-only count-summary meta truth-sync

## 변경 파일
- `tests/test_web_app.py` — `handle_chat` 의 실제 zero-strong-slot entity-card 런타임이 `session.web_search_history[0]` 를 `claim_coverage_summary: {strong:0, weak:0, missing>0}` 과 빈 `claim_coverage_progress_summary`, 그리고 downgraded `verification_label` 로 직렬화하는지 잠그는 focused 서비스 회귀 `test_handle_chat_zero_strong_slot_entity_card_history_badge_serialization_includes_missing_only_count_summary` 추가
- `e2e/tests/web-smoke.spec.mjs` — 신규 시나리오 `history-card entity-card zero-strong-slot 다시 불러오기 후 missing-only count-summary meta가 truthfully 유지됩니다` 추가. 디스크 record 의 `claim_coverage` 를 5 개 `missing` slot 으로 시드하고, client-seeded `claim_coverage_summary: {strong:0, weak:0, missing:5}` 로 render 한 뒤, click-reload 전/후 모두 history-card `.meta` 가 count-only 한 줄 `사실 검증 미확인 5` 로 유지되는지 잠금

## 사용 skill
- `round-handoff`
- `e2e-smoke-triage`

## 변경 이유
- 직전 `/work` (`2026-04-10-history-card-zero-strong-slot-entity-card-natural-reload-second-follow-up-continuity-closure.md`) 와 그 `/verify` 는 zero-strong natural-reload second-follow-up 의 `response_origin` / `source_paths` continuity 를 잠갔지만, 같은 round 의 verification 단계에서 실제 zero-strong runtime 과 기존 스모크 fixture 사이의 sync drift 가 발견되었음:
  - 실제 런타임: `response_origin.verification_label == "설명형 단일 출처"`, `response.claim_coverage` 길이 `5`, `history0.claim_coverage_summary == {strong:0, weak:0, missing:5}`, `claim_coverage_progress_summary == ""`
  - 기존 스모크: `claim_coverage: []`, `claim_coverage_summary` 미시드 — 즉 empty-claim-coverage 분기만 exercise
- `app/static/app.js:2225-2231` + `:2958-2969` 의 렌더러는 investigation 카드에서 `formatClaimCoverageCountSummary({missing:N})` → `"미확인 N"` 을 `사실 검증 미확인 N` detail line 으로 push 하고 `join(" · ")` 로 `.meta` 를 구성하므로, 실제 런타임은 `.meta` 에 `사실 검증 미확인 5` 한 줄이 관찰되어야 함. 기존 empty-summary fixture 는 이 런타임 분기를 전혀 exercise 하지 못함
- 이 슬라이스는 런타임 변경 없이 서비스 회귀 하나와 브라우저 스모크 하나로 zero-strong 가족의 **missing-only count-summary** 경로를 truth-sync 하는 범위임. natural-reload / source-path continuity / actual-search / dual-probe / noisy / latest-update / general / docs / pipeline 은 의도적으로 범위 밖이며, 기존 empty-summary negative 스모크도 건드리지 않음 (handoff 지시)

## 핵심 변경
1. **`tests/test_web_app.py` focused 서비스 회귀 추가**
   - `test_handle_chat_zero_strong_slot_entity_card_history_badge_serialization_includes_missing_only_count_summary`
     - 기존 `test_handle_chat_zero_strong_slot_entity_card_history_badge_serialization` 의 `_FakeWebSearchTool` / `AppSettings` / `WebAppService` fixture 를 그대로 재사용
     - 단일 `handle_chat({user_text})` 호출 후 `session.web_search_history[0]` 에서:
       - `verification_label != "설명형 다중 출처 합의"` 이고 빈 값이 아님 (downgraded label 유지)
       - `claim_coverage_summary.strong == 0`, `claim_coverage_summary.weak == 0`, `claim_coverage_summary.missing > 0` (missing-only 패턴)
       - `claim_coverage_progress_summary == ""` (zero-strong 경로의 빈 progress 유지)
     - 를 잠금. `missing` 의 정확한 값 대신 `> 0` 만 단언해 `_FakeWebSearchTool` 의 slot 분류 세부 변경에 대해 안정적인 failure-first 회귀를 보장함
2. **`e2e/tests/web-smoke.spec.mjs` 신규 브라우저 시나리오 추가**
   - 시나리오 이름: `history-card entity-card zero-strong-slot 다시 불러오기 후 missing-only count-summary meta가 truthfully 유지됩니다`
   - 디스크 record 의 `claim_coverage` 를 다섯 개의 `{slot, status:"missing", status_label:"미확인"}` 항목으로 시드 (기존 `[]` 에서 바꿈). `claim_coverage_progress_summary` 는 `""` 유지
   - `renderSearchHistory` item 에 `claim_coverage_summary: {strong: 0, weak: 0, missing: 5}` 와 `claim_coverage_progress_summary: ""` 를 시드 (기존 스모크에는 없었던 필드) — server 가 reload 후 `_summarize_claim_coverage` 로 동일한 `{missing:5}` 를 재직렬화하므로 client seed 와 server 결과가 일치
   - click-reload 전:
     - `.meta` 가 정확히 `toHaveText("사실 검증 미확인 5")`
     - `not.toContainText("설명 카드")` / `"최신 확인"` / `"일반 검색"` — entity_card investigation 이므로 answer-mode label 이 skip 되어야 함
     - `not.toContainText("·")` — single-category count segment 이므로 detailLines 가 한 줄뿐, ` · ` separator 가 전혀 등장해서는 안 됨
     - `preReloadMetaText.length > 0`, `startsWith("·") === false`, `endsWith("·") === false`
   - `다시 불러오기` 클릭 후:
     - `#response-origin-badge === "WEB"` + `web` class
     - `#response-answer-mode-badge` visible + `"설명 카드"`
     - `#response-origin-detail` 가 `설명형 단일 출처` / `백과 기반` 포함
     - `#context-box` 가 `namu.wiki` / `ko.wikipedia.org` 포함 (source-path continuity)
     - `.meta` 가 여전히 `"사실 검증 미확인 5"` 정확 문자열이고, answer-mode label 누출 없음, `·` separator 없음, leading/trailing separator artifact 없음
   - 기존 selector (`#search-history-box`, `.history-item`, `.meta`, `#response-origin-badge`, `#response-answer-mode-badge`, `#response-origin-detail`, `#context-box`) 와 `prepareSession`, `renderSearchHistory`, `fs/path` 헬퍼만 재사용했고 새 helper/selector/fixture 파일을 만들지 않음
   - 기존 empty-summary 스모크 `history-card entity-card zero-strong-slot 다시 불러오기 후 WEB badge, 설명 카드, 설명형 단일 출처, 백과 기반, namu.wiki/ko.wikipedia.org가 유지됩니다` 및 follow-up/second follow-up 은 전혀 건드리지 않음 (handoff 지시 — generic negative branch 유지)

## 검증
이번 라운드 실행:
- `python3 -m unittest -v tests.test_web_app.WebAppServiceTest.test_handle_chat_zero_strong_slot_entity_card_history_badge_serialization` → `ok`
- `python3 -m unittest -v tests.test_web_app.WebAppServiceTest.test_handle_chat_zero_strong_slot_entity_card_history_badge_serialization_includes_missing_only_count_summary` → `ok`
- `cd e2e && npx playwright test tests/web-smoke.spec.mjs -g "history-card entity-card zero-strong-slot 다시 불러오기 후 missing-only count-summary meta가 truthfully 유지됩니다" --reporter=line` → `1 passed (7.4s)`
- `git diff --check -- tests/test_web_app.py e2e/tests/web-smoke.spec.mjs work/4/10` → 출력 없음 (공백 오류 없음)

이번 라운드에서 재실행하지 않음:
- `python3 -m unittest -v tests.test_web_app` 전체 슈트 — 본 슬라이스는 기존 `handle_chat` 경로에 순수 추가 회귀만 붙였고 기존 로직 변경이 없음. handoff 도 focused 두 회귀만 재실행을 요구함
- broader Playwright suite 또는 `make e2e-test` — browser-visible contract 가 넓어지지 않았고 단일 신규 isolated scenario 하나만 추가함
- 기존 zero-strong empty-summary / follow-up / second follow-up 스모크 — handoff 는 이들을 그대로 두도록 명시함

## 남은 리스크
- 브라우저 `.meta` 잠금의 정확 N (5) 은 시드된 디스크 record 의 `missing` slot 개수에 의존함. 시드 배열을 수정하면 server 가 재직렬화하는 `missing` 카운트도 함께 바뀌므로 `toHaveText("사실 검증 미확인 5")` 를 같이 조정해야 함 — 이 의존성은 시드 배열 길이와 단일 지점에서 관리되므로 실수 여지가 제한적
- 서비스 회귀는 `missing > 0` 만 단언함. 실제 런타임이 empty-claim-coverage 경로로 드리프트하면 이 회귀가 먼저 실패해 원인을 가리킴 — 의도된 failure-first 설계. `missing` 의 정확 값을 고정하지 않아 `_FakeWebSearchTool` 내부 분류가 세부적으로 바뀌더라도 가짜 false-fail 을 내지 않음
- `formatClaimCoverageCountSummary({missing:N})` 이 현재 `"미확인 N"` 을 내고 `detailLines.join(" · ")` separator 가 ` · ` 라는 포맷 가정(`app/static/app.js:2225-2232`, `:2969`)에 의존함. 포맷이 바뀌면 이 스모크가 먼저 깨짐 — 같은 문자열이 다른 claim-coverage UI 곳에서도 사용 중이므로 drift 범위는 런타임 전반과 동일
- 본 슬라이스는 click-reload 분기만 다룸. 자연어 reload / first follow-up / second follow-up 에서 missing-only `.meta` 가 유지되는지는 별도 라운드로 남겨둠. handoff 도 이 범위를 의도적으로 좁혀 놓음
- 기존 empty-summary negative 스모크(`[]` claim_coverage + 빈 progress) 는 실제 런타임 branch 는 아니지만 `claim_coverage_summary` 가 완전히 비어 있을 때 `.meta` 가 생기지 않는 edge case 를 지키는 보조 회귀로 유지함. 본 슬라이스는 그것을 건드리지 않음
