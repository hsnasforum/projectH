# history-card zero-strong-slot entity-card natural-reload second-follow-up continuity closure

## 변경 파일
- `tests/test_web_app.py` — zero-strong-slot entity-card 자연어 reload → 첫 follow-up → 두 번째 follow-up 각 단계에서 stored `response_origin` 필드(`answer_mode`, `verification_label`, `source_roles`) 와 `active_context.source_paths` (`namu.wiki/w/testgame`, `ko.wikipedia.org/wiki/testgame`) 가 drift 없이 유지되는지 잠그는 focused 서비스 회귀 `test_handle_chat_zero_strong_slot_entity_card_natural_reload_second_follow_up_preserves_response_origin_and_source_paths` 추가
- `e2e/tests/web-smoke.spec.mjs` — 신규 시나리오 `entity-card zero-strong-slot 자연어 reload 후 두 번째 follow-up에서 WEB badge, 설명 카드, 설명형 단일 출처, 백과 기반, namu.wiki/ko.wikipedia.org가 drift하지 않습니다` 추가. 기존 zero-strong natural-reload follow-up 시나리오의 seed/흐름을 재사용해 click-reload → 자연어 reload → 첫 follow-up → 두 번째 follow-up 을 수행하고, 두 번째 follow-up 이후에도 WEB badge, `설명 카드`, `설명형 단일 출처`, `백과 기반`, `#context-box` 의 `namu.wiki`/`ko.wikipedia.org` 가 유지되는지 잠금

## 사용 skill
- `round-handoff`
- `e2e-smoke-triage`

## 변경 이유
- 직전 `/work` (`2026-04-10-history-card-simple-entity-card-natural-reload-claim-coverage-count-summary-continuity-closure.md`) 와 그 `/verify` 는 simple single-source entity-card 가족의 natural-reload second follow-up `claim_coverage_summary` continuity 를 잠갔음 (browser side = 시드된 `.meta` continuity, service side = non-dual-probe actual-entity-search count continuity)
- 같은 entity-card 계열 내부의 아직 잠기지 않은 current-risk 는 zero-strong-slot 의 **자연어 reload second follow-up** 경로: `tests/test_web_app.py:9661-9713` 은 자연어 reload exact fields 만, `:16622-16695` 는 first follow-up 만 잠갔고, click-reload 쪽은 second follow-up 까지 커버되어 있지만 natural-reload second follow-up 은 회귀/스모크 모두 빠져 있었음
- zero-strong 은 현재 shipped 된 특수 케이스임 — `claim_coverage` 가 비어 있고 verification label 이 `설명형 단일 출처` 로 downgrade 되어 사용자에게 그대로 노출되는 경로라서, 자연어 reload 에 이어지는 두 번째 follow-up 에서도 해당 downgraded entity-card semantics 가 유지되어야 함
- actual-search / dual-probe / noisy 가족은 이미 natural-reload second follow-up 커버리지가 있고, latest-update / general / stored-origin-missing fallback 은 본 슬라이스 범위 밖
- 이 슬라이스는 런타임 변경 없이 기존 zero-strong natural-reload follow-up 회귀/시나리오 패턴을 그대로 mirror 해 하나의 focused 서비스 회귀와 하나의 focused 브라우저 시나리오로 자연어 reload second follow-up gap 만 닫는 범위임

## 핵심 변경
1. **`tests/test_web_app.py` focused 서비스 회귀 추가**
   - `test_handle_chat_zero_strong_slot_entity_card_natural_reload_second_follow_up_preserves_response_origin_and_source_paths`
     - 첫 `handle_chat({user_text})` 호출 → zero-strong-slot entity-card baseline `response_origin` 추출
     - `handle_chat({user_text: "방금 검색한 결과 다시 보여줘"})` 자연어 reload 호출
     - `handle_chat({user_text + load_web_search_record_id})` 첫 follow-up 호출
     - `handle_chat({user_text + load_web_search_record_id})` 두 번째 follow-up 호출
     - 내부 헬퍼 `_assert_origin_and_sources(result, stage)` 로 각 단계에서:
       - `ok`
       - `actions_taken` 에 `load_web_search_record` 포함
       - `response_origin` non-null
       - `answer_mode in ("entity_card", first_origin["answer_mode"])`
       - `verification_label` 와 `source_roles` 가 first_origin 과 동일
       - `active_context.source_paths` 에 `https://namu.wiki/w/testgame` 와 `https://ko.wikipedia.org/wiki/testgame` 두 URL 모두 포함
       - 를 잠금
   - 기존 `test_handle_chat_zero_strong_slot_entity_card_natural_reload_follow_up_preserves_stored_response_origin` 의 `_FakeWebSearchTool`/`AppSettings`/`WebAppService` fixture 와 search result 구성을 그대로 재사용했고 신규 helper/import/fixture 파일은 추가하지 않음. 두 follow-up 은 서로 다른 `user_text` (`"이 검색 결과 요약해줘"` / `"이 게임 장르만 한 줄로 다시 정리해줘"`) 를 사용해 실제로 두 번 turn 이 발생하는지 확인함
2. **`e2e/tests/web-smoke.spec.mjs` 신규 브라우저 시나리오 추가**
   - 시나리오 이름: `entity-card zero-strong-slot 자연어 reload 후 두 번째 follow-up에서 WEB badge, 설명 카드, 설명형 단일 출처, 백과 기반, namu.wiki/ko.wikipedia.org가 drift하지 않습니다`
   - 기존 zero-strong natural-reload follow-up 시나리오의 seed record (`response_origin` 에 `provider/badge/label/answer_mode/verification_label/source_roles`, `claim_coverage: []`, `claim_coverage_progress_summary: ""`) 와 two-source fixture (`namu.wiki/w/testgame`, `ko.wikipedia.org/wiki/testgame`) 를 그대로 재사용
   - 흐름:
     - `renderSearchHistory` → `다시 불러오기` 클릭 (server 세션에 record 등록)
     - `sendRequest({ user_text: "방금 검색한 결과 다시 보여줘" })` 자연어 reload
     - `sendRequest({ user_text: "이 검색 결과 요약해줘", load_web_search_record_id })` 첫 follow-up (WEB badge, `설명 카드` 확인)
     - `sendRequest({ user_text: "이 게임 장르만 한 줄로 다시 정리해줘", load_web_search_record_id })` 두 번째 follow-up
   - 두 번째 follow-up 이후:
     - `#response-origin-badge === "WEB"` + `web` class
     - `#response-answer-mode-badge` visible + `"설명 카드"`
     - `#response-origin-detail` 가 `설명형 단일 출처` 와 `백과 기반` 포함
     - `#context-box` 가 `namu.wiki` 와 `ko.wikipedia.org` 두 URL 포함 (source-path continuity)
   - 기존 selector (`#search-history-box`, `.history-item-actions button.secondary`, `#response-origin-badge`, `#response-answer-mode-badge`, `#response-origin-detail`, `#context-box`) 와 `prepareSession`, `renderSearchHistory`, `sendRequest`, `fs/path` 헬퍼만 재사용했고 새 helper/selector/fixture 파일을 만들지 않음

## 검증
이번 라운드 실행:
- `python3 -m unittest -v tests.test_web_app.WebAppServiceTest.test_handle_chat_zero_strong_slot_entity_card_natural_reload_exact_fields` → `ok`
- `python3 -m unittest -v tests.test_web_app.WebAppServiceTest.test_handle_chat_zero_strong_slot_entity_card_natural_reload_follow_up_preserves_stored_response_origin` → `ok`
- `python3 -m unittest -v tests.test_web_app.WebAppServiceTest.test_handle_chat_zero_strong_slot_entity_card_natural_reload_second_follow_up_preserves_response_origin_and_source_paths` → `ok`
- `cd e2e && npx playwright test tests/web-smoke.spec.mjs -g "entity-card zero-strong-slot 자연어 reload 후 두 번째 follow-up에서 WEB badge, 설명 카드, 설명형 단일 출처, 백과 기반, namu.wiki/ko.wikipedia.org가 drift하지 않습니다" --reporter=line` → `1 passed (8.7s)`
- `git diff --check -- tests/test_web_app.py e2e/tests/web-smoke.spec.mjs work/4/10` → 출력 없음 (공백 오류 없음)

이번 라운드에서 재실행하지 않음:
- `python3 -m unittest -v tests.test_web_app` 전체 슈트 — 본 슬라이스는 기존 `handle_chat` 경로에 순수 추가 회귀만 붙였고 기존 로직 변경이 없음. handoff 도 focused 세 회귀만 재실행을 요구함
- broader Playwright suite 또는 `make e2e-test` — browser-visible contract 가 넓어지지 않았고 단일 신규 isolated scenario 하나만 추가함
- 다른 click-reload / claim-coverage count-summary / actual-search / dual-probe / noisy / latest-update / general 시나리오 — 이번 슬라이스는 zero-strong natural-reload second follow-up only 로 의도적으로 한정

## 남은 리스크
- 서비스 회귀의 `first_origin["answer_mode"]` 가 zero-strong 경로에서 `entity_card` 이외 값(`general` 등) 으로 drift 하면 `assertIn(..., ("entity_card", first_origin["answer_mode"]))` 가 첫 호출부터 실패해 원인을 빠르게 가리킴 — 의도된 failure-first 설계이며, 기존 follow-up 회귀도 동일한 assertion 을 사용함
- 내부 헬퍼 `_assert_origin_and_sources` 의 `result` 인자에는 `Any` 타입 힌트를 의도적으로 사용하지 않음 (`from typing import Any` 가 해당 파일 상단에 import 되어 있지 않음). Dict-like 구조를 전제로 한 assertion 시퀀스만 수행하며, 타입 오류가 생기면 각 assertion 이 우선 실패해 원인을 빠르게 가리킴
- zero-strong 의 `claim_coverage` 는 비어 있으므로 `_summarize_claim_coverage` 는 `{strong:0, weak:0, missing:0}` 을 반환함. 이 슬라이스는 count-summary 문자열 잠금이 아닌 `response_origin` / `source_paths` continuity 만 잠그므로 history-card `.meta` 내용에 대한 추가 어서션은 의도적으로 포함하지 않음
- click-reload second follow-up, simple single-source natural-reload second follow-up 은 이전 슬라이스들에서 이미 잠김. actual-search / dual-probe / noisy / latest-update / general / stored-origin-missing fallback 가족은 본 슬라이스 범위 밖
- 두 번째 follow-up 의 `user_text` 는 첫 follow-up 과 다른 문자열 (`"이 게임 장르만 한 줄로 다시 정리해줘"`) 을 사용함. 향후 `handle_chat` 내부에서 해당 문자열이 별도 intent 로 해석되어 reload-follow-up path 가 아닌 다른 경로로 빠지면 회귀의 `actions_taken` 단언에서 먼저 실패해 원인을 빠르게 가리킴
