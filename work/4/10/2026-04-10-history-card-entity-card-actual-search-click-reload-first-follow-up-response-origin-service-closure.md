# history-card entity-card actual-search click-reload first-follow-up response-origin service closure

## 변경 파일
- `tests/test_web_app.py` — 기존 `test_handle_chat_actual_entity_search_history_card_reload_second_follow_up_preserves_claim_coverage_count_summary` (`:9486`) 의 first follow-up 단계 (`third = service.handle_chat(...)` 직후) 에 exact `response_origin` 어서션 네 건을 추가:
  - `third_origin["badge"] == "WEB"`
  - `third_origin["answer_mode"] == "entity_card"`
  - `third_origin["verification_label"] == "설명형 다중 출처 합의"`
  - `third_origin["source_roles"] == ["백과 기반"]`
  - 기존 click reload → first follow-up → second follow-up 흐름, `_assert_strong_plus_missing_continuity` 헬퍼 호출 (`second`, `third`, `fourth` stage), exact count-summary `{strong:3, weak:0, missing:2}` + 빈 progress + `설명형 다중 출처 합의` history-entry 어서션은 전혀 건드리지 않음.
  - 설명형 주석으로 이 어서션이 browser smoke (`e2e/tests/web-smoke.spec.mjs:5020`, contract `WEB` / `설명 카드` / `설명형 다중 출처 합의` / `백과 기반`) 및 CONTROL_SEQ 68 의 click-reload second follow-up closure (`:17409`) 의 minimal inline 패턴과 truth-synced 임을 명시.
- `e2e/tests/web-smoke.spec.mjs` 는 전혀 건드리지 않음 (handoff 가 browser 쪽을 범위 밖으로 명시).

## 사용 skill
- `round-handoff`

## 변경 이유
- CONTROL_SEQ 68 (`2026-04-10-history-card-entity-card-actual-search-click-reload-second-follow-up-response-origin-service-closure.md`) 이 actual-search 가족의 click-reload **second** follow-up response_origin 을 browser smoke contract 와 같은 네 필드로 잠갔음.
- 그러나 actual-search click-reload **first** follow-up 단계의 서비스 층 response_origin 은 여전히 직접 잠기지 않은 상태였음:
  - `tests/test_web_app.py:9486` 는 기존에 history-entry 수준의 count-summary / progress / verification_label 연속성만 잠가두고, 각 stage 의 `response_origin` 필드는 검사하지 않았음.
  - `tests/test_web_app.py:16985` 는 store-seeded 경로라 실제 runtime strong-plus-missing 을 거치지 않음.
  - natural-reload actual-search follow-up 쪽은 `tests/test_web_app.py:18525` 에서 이미 response_origin continuity 가 강한 상태.
  - browser 쪽은 `e2e/tests/web-smoke.spec.mjs:5020` 에서 click-reload first follow-up 의 exact contract 를 이미 잠가둔 상태.
- handoff 는 이 단일 stage anchor 를 제자리에서 tighten 해 first follow-up `third["response"]["response_origin"]` 네 필드를 exact literal 로 잠그되, 기존 count-summary chain / stage flow / helper 호출 구조는 전혀 건드리지 않도록 지시. 범위 밖은 browser / 신규 테스트 / 다른 가족 / docs / pipeline / CONTROL_SEQ 68 이 이미 잠근 `:17409` 의 second follow-up closure.
- 본 라운드 이후 actual-search 가족의 click-reload first follow-up 경로가 browser smoke 의 네 필드 계약과 완전히 truth-synced 가 됨. click-reload chain 은 이제 show-only reload (`:9338-9352`) + first follow-up (본 라운드) + second follow-up (`:17409`) 세 stage 모두 response_origin literal 이 exact 로 잠긴 상태.

## 핵심 변경
1. **`tests/test_web_app.py:9486` first follow-up 블록 in-place tightening**
   - `third = service.handle_chat(...)` + `_assert_strong_plus_missing_continuity(third, "first follow-up")` 뒤에 `fourth = service.handle_chat(...)` 호출 이전 지점에 다음 어서션 블록을 삽입:
     - `third_origin = third["response"]["response_origin"]`
     - `assertEqual(third_origin["badge"], "WEB")`
     - `assertEqual(third_origin["answer_mode"], "entity_card")`
     - `assertEqual(third_origin["verification_label"], "설명형 다중 출처 합의")`
     - `assertEqual(third_origin["source_roles"], ["백과 기반"])`
   - 설명형 주석으로 browser smoke (`:5020`) contract + CONTROL_SEQ 68 의 minimal inline 패턴과의 정합성 의도 명시
   - `second` (show-only reload) / `fourth` (second follow-up) stage 의 helper 호출 및 신규/기존 어서션은 전혀 수정하지 않음
2. **helper 재사용 여부**
   - handoff 가 "do not duplicate a large helper if a few inline assertions after the `third = service.handle_chat(...)` call are enough" 라고 명시. CONTROL_SEQ 67 / 68 과 동일하게 helper 를 도입하지 않고 네 줄 inline 어서션 으로 minimal-diff 유지.
   - 기존 `_assert_strong_plus_missing_continuity(result, stage)` 헬퍼는 history-entry 수준의 count-summary / progress / verification_label 만 검사하고 `response_origin` 은 검사하지 않음. 본 라운드는 그 헬퍼를 수정하지 않고 first follow-up stage 한 곳에만 inline 어서션을 추가해 second/show-only reload stage 로의 drift 를 의도치 않게 유발하지 않도록 함.
3. **범위 밖 유지**
   - browser 시나리오 (`e2e/tests/web-smoke.spec.mjs:5020`) 는 이미 contract 를 잠가둔 상태로 그대로 유지
   - CONTROL_SEQ 68 의 `:17409` second follow-up closure 는 건드리지 않음
   - natural-reload actual-search follow-up anchor (`:18525`) 는 이미 강한 상태 — 건드리지 않음
   - zero-strong / dual-probe / noisy / latest-update / store-seeded / general 테스트는 전혀 수정하지 않음
   - docs, pipeline/config, 신규 테스트 생성 은 전혀 건드리지 않음

## 검증
이번 라운드 실행:
- `python3 -m unittest -v tests.test_web_app.WebAppServiceTest.test_handle_chat_actual_entity_search_history_card_reload_second_follow_up_preserves_claim_coverage_count_summary` → `ok` (신규 네 exact 어서션이 실제 actual-search click-reload first follow-up runtime 의 `response_origin` 과 정확히 일치: `badge == "WEB"`, `answer_mode == "entity_card"`, `verification_label == "설명형 다중 출처 합의"`, `source_roles == ["백과 기반"]`)
- `git diff --check -- tests/test_web_app.py work/4/10` → 출력 없음 (공백 오류 없음)

이번 라운드에서 재실행하지 않음:
- `python3 -m unittest -v tests.test_web_app` 전체 슈트 — handoff 가 focused 한 anchor 만 재실행을 요구했고, 본 슬라이스는 그 테스트 안에 네 줄짜리 어서션을 추가함
- Playwright 스위트 또는 `make e2e-test` — browser 측은 건드리지 않았고 browser smoke 는 이미 actual-search click-reload first follow-up contract 를 잠가둠
- `:17409` / `:18525` 등 이미 닫힌 anchor 들 — 본 슬라이스는 click-reload first follow-up stage 하나만 targets 함

## 남은 리스크
- 신규 네 exact 어서션은 actual-search runtime 이 click-reload first follow-up 단계에서도 `badge="WEB"` / `answer_mode="entity_card"` / `verification_label="설명형 다중 출처 합의"` / `source_roles=["백과 기반"]` 를 방출한다는 가정에 의존. drift 시 본 어서션이 먼저 깨져 browser smoke 와 silent 어긋남을 방지함.
- `source_roles == ["백과 기반"]` 은 browser smoke 의 source-role 배지 규약과 CONTROL_SEQ 59-62 / 68 의 actual-search 가족 계약과 truth-synced 상태. 향후 source_role 순서 / 중복 정책이 바뀌면 이 어서션이 먼저 깨짐.
- `third_origin` 은 `third["response"]["response_origin"]` 을 바로 조회. 기존 `_assert_strong_plus_missing_continuity` 헬퍼가 `third["ok"]` 를 이미 검사하므로 `None` 으로 통과하지 않음.
- show-only reload stage (`second`) 와 second follow-up stage (`fourth`) 의 response_origin 은 본 라운드에서 직접 잠기지 않음. show-only reload 는 `:9338-9352` 의 exact-fields anchor 가 1차 방어를 담당하고, second follow-up 은 `:17409` 의 CONTROL_SEQ 68 closure 가 잠가둔 상태. 따라서 click-reload chain 전 3 stage 가 서로 다른 테스트 anchor 로 drift detection 이 분산됨.
- CONTROL_SEQ 56-61 (noisy family full chain) + CONTROL_SEQ 62 (non-noisy actual-search chain) + CONTROL_SEQ 63 (dual-probe mixed-count chain) + CONTROL_SEQ 64 (zero-strong missing-only chain) + CONTROL_SEQ 65 (zero-strong initial+reload anchors) + CONTROL_SEQ 66 (zero-strong verification-label service continuity) + CONTROL_SEQ 67 (zero-strong click-reload second follow-up response-origin closure) + CONTROL_SEQ 68 (actual-search click-reload second follow-up response-origin closure) + 본 CONTROL_SEQ 69 (actual-search click-reload first follow-up response-origin closure) 루프는 entity-card 가족 네 주요 분기의 click-reload chain 전 stage 까지 browser + service 양쪽에서 완전 정합화함. 남은 가족은 latest-update / store-seeded / general 등.
- 본 라운드는 commit / push / PR / branch publish / next slice 선택 을 수행하지 않음. handoff 지시대로 한 슬라이스 종료 후 즉시 stop.
