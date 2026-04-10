# history-card entity-card actual-search click-reload second-follow-up response-origin service closure

## 변경 파일
- `tests/test_web_app.py` — 기존 `test_handle_chat_actual_entity_search_history_card_reload_second_follow_up_preserves_source_paths` (`:17409`) 의 final second follow-up 블록에 exact `response_origin` 어서션 네 건을 추가:
  - `fourth_origin["badge"] == "WEB"`
  - `fourth_origin["answer_mode"] == "entity_card"`
  - `fourth_origin["verification_label"] == "설명형 다중 출처 합의"`
  - `fourth_origin["source_roles"] == ["백과 기반"]`
  - 기존 click reload → first follow-up → second follow-up 흐름, `fourth["ok"]` 검사, `source_paths` 어서션 (`namu.wiki`/`ko.wikipedia.org`) 은 전혀 건드리지 않음.
  - 설명형 주석으로 이 어서션이 browser smoke (`e2e/tests/web-smoke.spec.mjs:5152`, contract `WEB` / `설명 카드` / `설명형 다중 출처 합의` / `백과 기반`) 및 CONTROL_SEQ 67 의 zero-strong click-reload second follow-up closure 의 minimal inline 패턴과 truth-synced 임을 명시.
- `e2e/tests/web-smoke.spec.mjs` 는 전혀 건드리지 않음 (handoff 가 browser 쪽을 범위 밖으로 명시).

## 사용 skill
- `round-handoff`

## 변경 이유
- CONTROL_SEQ 67 (`2026-04-10-history-card-entity-card-zero-strong-slot-click-reload-second-follow-up-response-origin-service-closure.md`) 이 zero-strong 가족의 click-reload second follow-up response_origin 을 literal `설명형 단일 출처` / `["백과 기반"]` / `entity_card` 로 잠갔음.
- actual-search (non-noisy multi-source agreement) 가족의 click-reload second follow-up 서비스 anchor 는 여전히 `active_context.source_paths` 두 URL 만 검사하고, `response_origin.badge` / `answer_mode` / `verification_label` / `source_roles` 는 직접 잠그지 않은 상태였음. 이 경우 second follow-up 에서 actual-search 가 다른 가족으로 drift 해도 (예: `verification_label == "설명형 단일 출처"`, `source_roles == []`) 테스트는 여전히 통과하면서 browser 계약과 silently 어긋남.
- browser 쪽은 `e2e/tests/web-smoke.spec.mjs:5152` 에서 이미 actual-search click-reload second follow-up 의 exact contract (`WEB`, `설명 카드`, `설명형 다중 출처 합의`, `백과 기반`) 를 잠가둔 상태.
- natural-reload actual-search second-follow-up 쪽은 이미 `tests/test_web_app.py:18588` 에서 response_origin continuity 를 강하게 잠가둔 상태. click-reload 경로만 마지막 loose anchor 로 남아 있었음.
- handoff 는 이 한 anchor 를 제자리에서 tighten 해 click-reload second follow-up 의 response_origin 네 필드를 exact literal 로 잠그되, 기존 `source_paths` 어서션과 stage 흐름은 그대로 두고, 범위 밖 (browser / 신규 테스트 / 다른 가족 / docs / pipeline) 은 건드리지 않도록 지시.
- 본 라운드 이후 actual-search 가족의 click-reload second follow-up 경로가 browser smoke 의 네 필드 계약과 완전히 truth-synced 가 됨. entity-card 가족 주요 분기 (noisy strong-plus-missing / non-noisy actual-search / dual-probe mixed / zero-strong missing-only) 의 서비스 층 drift detection 마지막 누락 stage 하나가 더 폐쇄됨.

## 핵심 변경
1. **`tests/test_web_app.py:17409` final second follow-up 블록 in-place tightening**
   - 기존 어서션 유지: `self.assertTrue(fourth["ok"])`, `source_paths = fourth["session"]["active_context"]["source_paths"]`, `assertIn("https://namu.wiki/w/...", source_paths)`, `assertIn("https://ko.wikipedia.org/wiki/...", source_paths)`
   - 추가: `fourth_origin = fourth["response"]["response_origin"]` + 네 exact 어서션:
     - `assertEqual(fourth_origin["badge"], "WEB")`
     - `assertEqual(fourth_origin["answer_mode"], "entity_card")`
     - `assertEqual(fourth_origin["verification_label"], "설명형 다중 출처 합의")`
     - `assertEqual(fourth_origin["source_roles"], ["백과 기반"])`
   - 설명형 주석으로 browser smoke (`:5152`) contract 와 CONTROL_SEQ 67 의 minimal inline 패턴과의 정합성 의도를 명시
   - 기존 click reload → first follow-up → second follow-up flow (`second`, `third`, `fourth` handle_chat 호출) 는 전혀 수정하지 않음
2. **helper 재사용 여부**
   - handoff 가 "mirror the minimal inline pattern used in the just-closed zero-strong service closure rather than introducing a new helper" 라고 명시. CONTROL_SEQ 67 과 동일하게 helper 를 도입하지 않고 네 줄 inline 어서션 으로 minimal-diff 유지.
   - actual-search 는 zero-strong 과 달리 `badge == "WEB"` 어서션을 한 줄 더 포함 (CONTROL_SEQ 67 은 badge 어서션을 포함하지 않았음). handoff 가 "badge == 'WEB'" 을 명시적으로 요구했기 때문.
3. **범위 밖 유지**
   - browser 시나리오 (`e2e/tests/web-smoke.spec.mjs:5152`) 는 이미 contract 를 잠가둔 상태로 그대로 유지
   - natural-reload actual-search second-follow-up anchor (`tests/test_web_app.py:18588`) 는 이미 강한 상태 — 건드리지 않음
   - zero-strong / noisy / dual-probe / latest-update / store-seeded / general 테스트는 전혀 수정하지 않음
   - docs, pipeline/config, 신규 테스트 생성 은 전혀 건드리지 않음

## 검증
이번 라운드 실행:
- `python3 -m unittest -v tests.test_web_app.WebAppServiceTest.test_handle_chat_actual_entity_search_history_card_reload_second_follow_up_preserves_source_paths` → `ok` (신규 네 exact 어서션이 실제 actual-search click-reload second follow-up runtime 의 `response_origin` 과 정확히 일치: `badge == "WEB"`, `answer_mode == "entity_card"`, `verification_label == "설명형 다중 출처 합의"`, `source_roles == ["백과 기반"]`)
- `git diff --check -- tests/test_web_app.py work/4/10` → 출력 없음 (공백 오류 없음)

이번 라운드에서 재실행하지 않음:
- `python3 -m unittest -v tests.test_web_app` 전체 슈트 — handoff 가 focused 한 anchor 만 재실행을 요구했고, 본 슬라이스는 그 테스트 안에 네 줄짜리 어서션을 추가함
- Playwright 스위트 또는 `make e2e-test` — browser 측은 건드리지 않았고 browser smoke 는 이미 actual-search click-reload second follow-up contract 를 잠가둠
- natural-reload actual-search second follow-up 및 다른 closed anchors — 본 슬라이스는 click-reload 경로 하나만 targets 함

## 남은 리스크
- 신규 네 exact 어서션은 actual-search runtime 이 click-reload second follow-up 단계에서도 `badge="WEB"` / `answer_mode="entity_card"` / `verification_label="설명형 다중 출처 합의"` / `source_roles=["백과 기반"]` 를 방출한다는 가정에 의존. drift 시 본 어서션이 먼저 깨져 browser smoke 와 silent 어긋남을 방지함.
- `source_roles == ["백과 기반"]` 은 browser smoke 의 source-role 배지 규약과 CONTROL_SEQ 59-62 의 actual-search 가족 계약과 truth-synced 상태. 향후 source_role 순서 / 중복 정책이 바뀌면 이 어서션이 먼저 깨짐.
- `fourth_origin` 은 `fourth["response"]["response_origin"]` 을 바로 조회. `None` 이면 exact equality 가 즉시 실패하므로 fallback 은 불필요. 기존 테스트가 `fourth["ok"]` 가 True 임을 이미 검사함.
- helper 를 복제하지 않은 이유는 click-reload 흐름의 second follow-up 한 stage 에서만 tighten 이 필요하기 때문. 향후 click-reload 흐름의 다른 stage 도 tighten 이 필요해지면 helper 로 승격 검토.
- CONTROL_SEQ 56-61 (noisy family full chain) + CONTROL_SEQ 62 (non-noisy actual-search chain) + CONTROL_SEQ 63 (dual-probe mixed-count chain) + CONTROL_SEQ 64 (zero-strong missing-only chain) + CONTROL_SEQ 65 (zero-strong initial+reload anchors) + CONTROL_SEQ 66 (zero-strong verification-label service continuity) + CONTROL_SEQ 67 (zero-strong click-reload second follow-up response-origin closure) + 본 CONTROL_SEQ 68 (actual-search click-reload second follow-up response-origin closure) 루프는 entity-card 가족 네 주요 분기의 click-reload second follow-up 단계까지 browser + service 양쪽에서 완전 정합화함. 남은 가족은 latest-update / store-seeded / general 등.
- 본 라운드는 commit / push / PR / branch publish / next slice 선택 을 수행하지 않음. handoff 지시대로 한 슬라이스 종료 후 즉시 stop.
