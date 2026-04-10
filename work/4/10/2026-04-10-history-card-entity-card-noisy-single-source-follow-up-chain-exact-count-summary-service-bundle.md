# history-card entity-card noisy single-source follow-up-chain exact count-summary service bundle

## 변경 파일
- `tests/test_web_app.py` — 기존 noisy entity-card follow-up 서비스 테스트 네 개에서 broad count-pattern 블록 (`assertGreater(strong>0)` + `assertEqual(weak==0)` + `assertGreater(missing>0)`) 을 exact equality (`claim_coverage_summary == {"strong": 3, "weak": 0, "missing": 2}`) 로 교체:
  - `test_handle_chat_entity_card_noisy_single_source_claim_excluded_after_natural_reload_follow_up` (자연어 reload → first follow-up)
  - `test_handle_chat_entity_card_noisy_single_source_claim_excluded_after_natural_reload_second_follow_up` (자연어 reload → second follow-up)
  - `test_handle_chat_entity_card_noisy_single_source_claim_excluded_after_history_card_reload_follow_up` (click reload → first follow-up)
  - `test_handle_chat_entity_card_noisy_single_source_claim_excluded_after_history_card_reload_second_follow_up` (click reload → second follow-up)
  - 네 테스트의 기존 `verification_label == "설명형 다중 출처 합의"` / `claim_coverage_progress_summary == ""` / 텍스트 / 원본 / source_roles / source_paths / `출시일`/`2025`/`blog.example.com` 제외 어서션은 전혀 건드리지 않음
- `e2e/tests/web-smoke.spec.mjs` 는 전혀 건드리지 않음 (handoff 가 browser 쪽을 범위 밖으로 명시). CONTROL_SEQ 57/58 이 잠근 browser `.meta` 계약은 그대로 유지됨.

## 사용 skill
- `round-handoff`

## 변경 이유
- CONTROL_SEQ 59 (direct reload service × 2) + CONTROL_SEQ 60 (initial response service × 2) 이 noisy entity-card strong-plus-missing 분기를 service 층의 첫 응답 / 직접 reload 단계에서 exact equality `{"strong": 3, "weak": 0, "missing": 2}` 로 잠갔음.
- 그러나 follow-up 체인 네 테스트 (`:19499`, `:19574`, `:19653`, `:19729`) 는 여전히 loose count pattern (`strong>0`, `weak==0`, `missing>0`) 만 어서션하고 있어, `{3,0,2}` 와 다른 shape (예: `{2,0,3}`, `{4,0,1}`, `{3,1,1}`) 로 drift 해도 이 테스트들은 통과하는 상태였음.
- handoff 는 "smallest coherent next slice is to tighten these four existing service tests in place rather than adding more browser clones" 라고 명시하고, follow-up 체인의 loose count pattern 을 initial / reload 단계와 동일한 exact equality 로 정합화하라고 지시함.
- browser 측 follow-up `.meta` truth 는 이미 기존 browser 시나리오들에서 잠겨 있으므로 본 라운드는 service 층에서만 exact equality 를 적용하면 전 단계 (initial → reload → first follow-up → second follow-up) 가 서비스 층에서 동일 payload shape `{3,0,2}` 를 공유하게 됨.
- 네 테스트는 구조가 동일한 broad count pattern 블록 하나를 공유하므로 `replace_all` 로 한 번에 exact equality 로 교체 가능하고 duplicate 테스트를 만들 필요가 없음.

## 핵심 변경
1. **`tests/test_web_app.py` broad count pattern → exact equality 일괄 교체**
   - 교체 대상 (네 테스트에서 반복되는 블록):
     ```python
     noisy_count = noisy_entry.get("claim_coverage_summary") or {}
     self.assertGreater(int(noisy_count.get("strong") or 0), 0)
     self.assertEqual(int(noisy_count.get("weak") or 0), 0)
     self.assertGreater(int(noisy_count.get("missing") or 0), 0)
     ```
   - 교체 결과:
     ```python
     self.assertEqual(
         noisy_entry.get("claim_coverage_summary"),
         {"strong": 3, "weak": 0, "missing": 2},
     )
     ```
   - `Edit` 의 `replace_all=true` 옵션으로 네 테스트의 블록을 한 번에 교체. 다른 가족 (latest-update, store-seeded 등) 은 이 정확한 블록 pattern 을 공유하지 않으므로 안전.
   - `noisy_entry.get("claim_coverage_summary")` 가 `None` 이면 exact equality 가 즉시 실패하므로 기존 `or {}` fallback 은 불필요해지고 오히려 방해되는 구조.
2. **기존 어서션은 그대로 유지**
   - `noisy_entry["verification_label"] == "설명형 다중 출처 합의"` (exact equality 로 이미 잠긴 상태)
   - `str(noisy_entry.get("claim_coverage_progress_summary") or "") == ""`
   - `third/fourth["response"]["text"]` 의 `"출시일"` / `"2025"` / `"blog.example.com"` 제외
   - `response_origin.badge` / `answer_mode` / `verification_label` / `source_roles`
   - `active_context.source_paths` 의 nwki / wikipedia / blog.example.com 포함
3. **범위 밖 유지**
   - `e2e/tests/web-smoke.spec.mjs`, latest-update, dual-probe, zero-count, docs, pipeline/config, 신규 테스트 생성 은 전혀 건드리지 않음 (handoff 지시)
   - CONTROL_SEQ 59/60 에서 잠근 initial response / direct reload service 어서션도 그대로 유지

## 검증
이번 라운드 실행:
- `python3 -m unittest -v tests.test_web_app.WebAppServiceTest.test_handle_chat_entity_card_noisy_single_source_claim_excluded_after_natural_reload_follow_up tests.test_web_app.WebAppServiceTest.test_handle_chat_entity_card_noisy_single_source_claim_excluded_after_natural_reload_second_follow_up tests.test_web_app.WebAppServiceTest.test_handle_chat_entity_card_noisy_single_source_claim_excluded_after_history_card_reload_follow_up tests.test_web_app.WebAppServiceTest.test_handle_chat_entity_card_noisy_single_source_claim_excluded_after_history_card_reload_second_follow_up` → 네 테스트 모두 `ok` (신규 exact equality 어서션이 실제 follow-up 체인 runtime 에서 `{strong:3, weak:0, missing:2}` 와 정확히 일치함을 확인)
- `git diff --check -- tests/test_web_app.py work/4/10` → 출력 없음 (공백 오류 없음)

이번 라운드에서 재실행하지 않음:
- `python3 -m unittest -v tests.test_web_app` 전체 슈트 — handoff 가 focused 네 follow-up anchor 만 재실행을 요구했고, 본 슬라이스는 네 테스트 안에서만 count pattern 을 교체함
- Playwright 스위트 또는 `make e2e-test` — browser 측은 건드리지 않았고 CONTROL_SEQ 57/58 이 noisy entity-card browser `.meta` 계약을 이미 잠가둠
- 기존 initial response / direct reload anchors (`:11118`, `:11263`) — 본 슬라이스는 follow-up 체인만 targets 하므로 이전 라운드의 어서션을 다시 실행할 필요 없음

## 남은 리스크
- 신규 `claim_coverage_summary == {"strong": 3, "weak": 0, "missing": 2}` exact equality 는 noisy entity-card runtime 분포 (`장르`/`개발사`/`플랫폼`/`엔진`/`난이도` 또는 동일한 5-slot 분포) 가 strong 3 / weak 0 / missing 2 로 고정되어 있음에 의존. noisy 제외 정책이나 slot 구성이 바뀌면 네 어서션이 동시에 깨져 drift 를 가리킴 — 이것이 본 라운드의 설계 의도 (loose pattern 이 가리던 shape drift 를 exact equality 로 노출).
- CONTROL_SEQ 56-58 (browser) + CONTROL_SEQ 59-60 (service initial response + direct reload) + 본 CONTROL_SEQ 61 (service follow-up chain × 4) 루프는 noisy entity-card strong-plus-missing 분기를 browser initial-render / browser reload-only / service initial response / service direct reload / service natural reload first follow-up / service natural reload second follow-up / service click reload first follow-up / service click reload second follow-up 여덟 축에서 truth-synced 로 잠그는 진행 패턴으로 완성됨.
- 본 라운드는 기존 loose pattern 을 exact equality 로 교체한 형태라 테스트 수는 불변이고 새 코드 path 도 추가되지 않음. runtime 동작 / 직렬화 로직 / 렌더러 는 전혀 변경되지 않음.
- `noisy_count` 지역 변수가 제거되면서 각 테스트 블록의 변수 scope 가 조금 축소됐지만 이후 해당 블록에서 `noisy_count` 를 사용하는 다른 코드는 없음 (확인됨).
- handoff 가 "Do not widen into browser scenarios, latest-update, dual-probe, zero-count, docs, or pipeline/config work" 라고 명시했고 본 라운드는 그 지시를 정확히 지킴.
- 본 라운드는 commit / push / PR / branch publish / next slice 선택 을 수행하지 않음. handoff 지시대로 한 슬라이스 종료 후 즉시 stop.
