# history-card entity-card zero-strong-slot click-reload second-follow-up response-origin service closure

## 변경 파일
- `tests/test_web_app.py` — 기존 `test_handle_chat_zero_strong_slot_entity_card_history_card_reload_second_follow_up_preserves_source_paths` (`:17894`) 의 final second follow-up 블록에 exact `response_origin` 어서션 세 건을 추가:
  - `fourth_origin["answer_mode"] == "entity_card"`
  - `fourth_origin["verification_label"] == "설명형 단일 출처"`
  - `fourth_origin["source_roles"] == ["백과 기반"]`
  - 기존 click reload → first follow-up → second follow-up 흐름, `fourth["ok"]` 검사, `source_paths` 어서션 (`namu.wiki/testgame`, `ko.wikipedia.org/testgame`) 은 전혀 건드리지 않음.
  - 설명형 주석으로 이 어서션이 browser `.meta` smoke (`사실 검증 미확인 5`) + literal label smoke (`설명형 단일 출처`) + CONTROL_SEQ 64-66 에서 잠근 zero-strong 가족 service-side 계약과 truth-synced 임을 명시.
- `e2e/tests/web-smoke.spec.mjs` 는 전혀 건드리지 않음 (handoff 가 browser 쪽을 범위 밖으로 명시).

## 사용 skill
- `round-handoff`

## 변경 이유
- CONTROL_SEQ 64 (zero-strong follow-up chain exact count `{0,0,5}`), CONTROL_SEQ 65 (zero-strong initial + reload-only exact count-summary + 빈 progress), CONTROL_SEQ 66 (zero-strong literal `"설명형 단일 출처"` service continuity for initial / reload / follow-up chain 일곱 테스트) 까지 진행돼 zero-strong 가족의 서비스 층 계약이 count-summary / progress / label / answer_mode / source_roles / source_paths 여섯 축에서 거의 완성된 상태.
- 그러나 `test_handle_chat_zero_strong_slot_entity_card_history_card_reload_second_follow_up_preserves_source_paths` (`:17894`) 는 여전히 `active_context.source_paths` 두 URL 만 검사하고, click reload 이후 second follow-up 단계에서 `response_origin.answer_mode` / `verification_label` / `source_roles` 는 직접 잠그지 않은 상태로 남아 있었음. 이 경우 second follow-up 에서 response_origin 필드가 다른 가족으로 drift 해도 (예: `answer_mode == "latest_update"`, `verification_label == "설명형 다중 출처 합의"`, `source_roles == []`) 테스트는 여전히 통과하면서 browser literal 과 silently 어긋남.
- browser 쪽은 이미 `e2e/tests/web-smoke.spec.mjs:6410` + `:6523` 에서 literal label `설명형 단일 출처` 와 `.meta` line `사실 검증 미확인 5` 를 click-reload second follow-up 단계까지 exact 로 잠가둔 상태.
- handoff 는 이 하나의 anchor 를 제자리에서 tighten 해 click-reload second follow-up 단계의 response_origin 세 필드를 browser 계약과 같은 값으로 직접 잠그되, 기존 `source_paths` 어서션과 click reload → first follow-up → second follow-up 흐름은 그대로 두고, 범위 밖 (browser / 신규 테스트 / 다른 가족 / docs / pipeline) 은 건드리지 않도록 지시함.
- 본 라운드 이후 zero-strong 가족의 click-reload second follow-up 경로가 browser `.meta` + literal label + service answer_mode + service verification_label + service source_roles + service source_paths 여섯 축에서 완전히 truth-synced 가 됨. zero-strong 가족 전체의 서비스 층 drift detection 이 마지막 누락 stage 까지 폐쇄됨.

## 핵심 변경
1. **`tests/test_web_app.py:17894` final second follow-up 블록 in-place tightening**
   - 기존 어서션 유지: `self.assertTrue(fourth["ok"])`, `source_paths = fourth["session"]["active_context"]["source_paths"]`, `assertIn("https://namu.wiki/w/testgame", source_paths)`, `assertIn("https://ko.wikipedia.org/wiki/testgame", source_paths)`
   - 추가: `fourth_origin = fourth["response"]["response_origin"]` + 세 exact 어서션:
     - `assertEqual(fourth_origin["answer_mode"], "entity_card")`
     - `assertEqual(fourth_origin["verification_label"], "설명형 단일 출처")`
     - `assertEqual(fourth_origin["source_roles"], ["백과 기반"])`
   - 설명형 주석으로 browser smoke + CONTROL_SEQ 64-66 과의 정합성 의도를 명시
   - 기존 click reload → first follow-up → second follow-up flow (`second`, `third`, `fourth` handle_chat 호출) 는 전혀 수정하지 않음
2. **helper 재사용 여부**
   - 인접한 `test_handle_chat_zero_strong_slot_entity_card_natural_reload_second_follow_up_preserves_response_origin_and_source_paths` (`:18053`) 의 `_assert_origin_and_sources` 헬퍼 패턴을 그대로 복제하지 않고, 최소 inline 어서션 세 줄만 추가하는 minimal-diff 접근을 선택. handoff 가 "do not duplicate large helper code if a minimal inline assertion is enough" 라고 명시.
   - `first_origin` continuity 방식 대신 literal 값에 대한 direct exact 비교를 선택한 이유는 browser 측이 이미 literal 값을 잠가둔 상태이고 CONTROL_SEQ 66 에서 natural-reload second follow-up 의 `first_origin` 을 literal 에 고정했기 때문. 두 패턴 모두 동일한 drift coverage 를 제공하지만 direct 비교가 이 단 한 줄짜리 closure 에서 가장 작은 diff.
3. **범위 밖 유지**
   - browser 시나리오 (`e2e/tests/web-smoke.spec.mjs:6410`, `:6523`) 는 이미 literal label + `.meta` 를 잠가둔 상태로 그대로 유지
   - CONTROL_SEQ 64 / 65 / 66 이 잠근 count-summary `{0,0,5}` / 빈 progress / source_roles / answer_mode / verification_label / source_paths 어서션은 전혀 건드리지 않음
   - noisy / actual-search / dual-probe / latest-update / store-seeded / general 테스트는 전혀 수정하지 않음
   - docs, pipeline/config, 신규 테스트 생성 은 전혀 건드리지 않음

## 검증
이번 라운드 실행:
- `python3 -m unittest -v tests.test_web_app.WebAppServiceTest.test_handle_chat_zero_strong_slot_entity_card_history_card_reload_second_follow_up_preserves_source_paths` → `ok` (신규 세 exact 어서션이 실제 zero-strong click-reload second follow-up runtime 의 `response_origin` 과 정확히 일치: `answer_mode == "entity_card"`, `verification_label == "설명형 단일 출처"`, `source_roles == ["백과 기반"]`)
- `git diff --check -- tests/test_web_app.py work/4/10` → 출력 없음 (공백 오류 없음)

이번 라운드에서 재실행하지 않음:
- `python3 -m unittest -v tests.test_web_app` 전체 슈트 — handoff 가 focused 한 anchor 만 재실행을 요구했고, 본 슬라이스는 그 테스트 안에 세 줄짜리 어서션을 추가함
- Playwright 스위트 또는 `make e2e-test` — browser 측은 건드리지 않았고 browser smoke 는 이미 click-reload second follow-up UX 를 잠가둠
- CONTROL_SEQ 64-66 이 잠근 다른 zero-strong 테스트 — 본 슬라이스는 마지막 click-reload second follow-up closure 만 targets 함

## 남은 리스크
- 신규 `fourth_origin["verification_label"] == "설명형 단일 출처"` / `answer_mode == "entity_card"` / `source_roles == ["백과 기반"]` 세 exact 어서션은 zero-strong runtime 이 click-reload second follow-up 단계에서도 이 literal 값을 계속 방출한다는 가정에 의존. drift 시 본 어서션이 먼저 깨져 browser smoke 와 silent 어긋남을 방지함.
- `source_roles == ["백과 기반"]` 은 browser smoke 의 source-role 배지 규약 및 CONTROL_SEQ 66 의 literal `설명형 단일 출처` 계약과 truth-synced 상태. 향후 source_role 순서 / 중복 정책이 바뀌면 이 어서션이 먼저 깨짐.
- `fourth_origin` 은 `fourth["response"]["response_origin"]` 을 바로 조회. `None` 이면 exact equality 가 즉시 실패하므로 fallback 은 불필요. 기존 테스트가 `fourth["ok"]` 가 True 임을 이미 검사하므로 response_origin 이 누락된 상태로 통과하지는 않음.
- `_assert_origin_and_sources` 헬퍼를 복제하지 않은 이유: 본 테스트는 click reload → first follow-up → second follow-up 중 final stage 한 곳만 tighten 하면 되므로 stage-반복 helper 가 불필요했음. 향후 click reload 흐름의 다른 stage 도 tighten 이 필요해지면 그때 helper 로 승격 검토.
- CONTROL_SEQ 56-61 (noisy family full chain) + CONTROL_SEQ 62 (non-noisy actual-search chain) + CONTROL_SEQ 63 (dual-probe mixed-count chain) + CONTROL_SEQ 64 (zero-strong missing-only chain) + CONTROL_SEQ 65 (zero-strong initial+reload anchors) + CONTROL_SEQ 66 (zero-strong verification-label service continuity) + 본 CONTROL_SEQ 67 (zero-strong click-reload second follow-up response-origin closure) 루프로 zero-strong 가족의 서비스 층 drift detection 이 완전히 폐쇄됨. 남은 가족은 latest-update / store-seeded / general 등.
- 본 라운드는 commit / push / PR / branch publish / next slice 선택 을 수행하지 않음. handoff 지시대로 한 슬라이스 종료 후 즉시 stop.
