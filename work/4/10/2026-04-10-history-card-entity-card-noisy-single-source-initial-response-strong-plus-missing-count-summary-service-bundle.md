# history-card entity-card noisy single-source initial-response strong-plus-missing count-summary service bundle

## 변경 파일
- `tests/test_web_app.py` — 기존 noisy entity-card 직접 reload 서비스 테스트 두 개의 **첫 응답** 블록을 제자리에서 tighten:
  - `:11118` `test_handle_chat_entity_card_multi_source_agreement_retained_after_history_card_reload` — 첫 응답의 noisy 제외 어서션 뒤, reload 호출 직전에 baseline history summary 어서션 추가
  - `:11263` `test_handle_chat_entity_card_multi_source_agreement_over_noise_natural_reload` — 기존 `first_history = first["session"]["web_search_history"][0]` + `source_roles` 어서션 뒤에 baseline history summary 어서션 추가
  - 두 곳 모두 신규 어서션은 동일한 세 계약을 direct 로 잠금:
    - `first_history["verification_label"] == "설명형 다중 출처 합의"`
    - `first_history["claim_coverage_summary"] == {"strong": 3, "weak": 0, "missing": 2}`
    - `first_history["claim_coverage_progress_summary"] == ""`
  - 기존 reload 단계 (CONTROL_SEQ 59) 에서 잠근 어서션 블록은 전혀 건드리지 않음
- `e2e/tests/web-smoke.spec.mjs` 는 전혀 건드리지 않음 (handoff 가 browser 쪽을 범위 밖으로 명시). 기존 `:2503` / `:2601` 의 initial-render `.meta` 어서션 (CONTROL_SEQ 57) 과 `:2615` 의 show-only reload `.meta` 어서션 (CONTROL_SEQ 58) 이 그대로 잠겨 있음.

## 사용 skill
- `round-handoff`

## 변경 이유
- CONTROL_SEQ 59 (`2026-04-10-history-card-entity-card-noisy-single-source-direct-reload-strong-plus-missing-count-summary-service-bundle.md`) 가 직접 reload 단계의 `session.web_search_history[0]` 에 대해 `verification_label` / `claim_coverage_summary` / `claim_coverage_progress_summary` 세 계약을 잠갔지만, 같은 두 테스트의 **첫 응답** 단계에서는 이 세 계약이 여전히 간접적으로만 증명되어 있었음.
- handoff 는 "Do not reopen the already-closed reload browser/service slice" 라고 명시하고, 가장 인접한 next same-family current-risk 로 **first response baseline** 를 같은 service 층에서 직접 잠그는 범위를 지목함.
- browser 쪽은 CONTROL_SEQ 57 (initial-render noisy strong-plus-missing `.meta` exact text) 에서 이미 shipped strong-plus-missing 분기를 pre-click initial-render 단계에서 잠가둔 상태. 본 라운드는 그 browser initial-render truth 와 **service 측 초기 응답 truth** 가 같은 payload shape (`{strong:3, weak:0, missing:2}`, 빈 progress, `설명형 다중 출처 합의`) 를 공유함을 service 층에서 직접 어서션해 truth-synced 상태로 만듦.
- 두 기존 테스트는 이미 정확히 필요한 첫 응답을 구성하므로 duplicate 테스트를 만들지 않고 in-place tighten 만으로 범위가 충분함.

## 핵심 변경
1. **`tests/test_web_app.py:11118` 첫 응답 블록 in-place tightening**
   - 기존 `self.assertNotIn("2025", first_text, ...)` 뒤, `"--- 둘째 호출: load_web_search_record_id reload ---"` 주석 직전에 baseline history summary 블록을 추가:
     - `first_history = first["session"]["web_search_history"][0]`
     - `assertEqual(first_history["verification_label"], "설명형 다중 출처 합의")`
     - `assertEqual(first_history["claim_coverage_summary"], {"strong": 3, "weak": 0, "missing": 2})`
     - `assertEqual(first_history["claim_coverage_progress_summary"], "")`
   - 설명형 주석으로 이 어서션이 최초 응답 시점에서부터 noisy entity-card strong-plus-missing 분기 계약을 잠금 의도임을 명시
2. **`tests/test_web_app.py:11263` 첫 응답 블록 in-place tightening**
   - 기존 `first_history = first["session"]["web_search_history"][0]` + `self.assertEqual(first_history["source_roles"], ["백과 기반"])` 뒤에 동일한 세 어서션을 추가 (`first_history` 는 이미 bound 되어 있으므로 재조회하지 않음).
   - 설명형 주석으로 같은 의도를 명시
3. **기존 reload 단계 어서션은 전혀 건드리지 않음**
   - CONTROL_SEQ 59 에서 각 테스트의 `second["session"]["web_search_history"][0]` 에 대해 추가한 reload 단계 세 어서션은 그대로 유지
   - 기존 첫 응답의 strong slot 유지 / `확인된 사실 [교차 확인]:` 본문 / noisy `출시일`/`2025`/`blog.example.com` 제외 / `source_roles` / response_origin exact fields 는 전혀 수정하지 않음
4. **범위 밖 유지**
   - `e2e/tests/web-smoke.spec.mjs`, latest-update, dual-probe, zero-count, docs, pipeline/config, 신규 테스트 생성 은 전혀 건드리지 않음 (handoff 지시)

## 검증
이번 라운드 실행:
- `python3 -m unittest -v tests.test_web_app.WebAppServiceTest.test_handle_chat_entity_card_multi_source_agreement_retained_after_history_card_reload tests.test_web_app.WebAppServiceTest.test_handle_chat_entity_card_multi_source_agreement_over_noise_natural_reload` → 두 테스트 모두 `ok` (신규 baseline history summary 어서션이 실제 첫 응답 runtime 에서 `{strong:3, weak:0, missing:2}` + 빈 progress + 설명형 다중 출처 합의 분기와 정확히 일치함을 확인)
- `git diff --check -- tests/test_web_app.py work/4/10` → 출력 없음 (공백 오류 없음)

이번 라운드에서 재실행하지 않음:
- `python3 -m unittest -v tests.test_web_app` 전체 슈트 — handoff 가 focused 두 service anchor 만 재실행을 요구했고, 본 슬라이스는 같은 두 테스트 안에서만 첫 응답 블록을 확장함
- Playwright 스위트 또는 `make e2e-test` — browser 측은 건드리지 않았고 CONTROL_SEQ 57/58 이 noisy entity-card browser `.meta` 계약을 이미 잠가둠
- 기존 `:19532`, `:19687` 등 follow-up 체인 회귀 — 본 슬라이스는 첫 응답 단계만 tighten 하므로 follow-up 체인을 다시 실행할 필요 없음

## 남은 리스크
- 신규 `first_history["claim_coverage_summary"] == {"strong": 3, "weak": 0, "missing": 2}` 어서션은 `_summarize_claim_coverage` 의 key 규약(`strong`/`weak`/`missing`) 과 값 타입(int) 에 의존. `CoverageStatus` StrEnum 이 dict equality 에서 plain string 과 같게 비교되므로 runtime 에서 정확히 일치함. key 이름이나 타입이 바뀌면 본 어서션이 먼저 깨져 drift 를 가리킴.
- `claim_coverage_progress_summary == ""` 는 noisy 제외된 strong-plus-missing 분포에서 progress summary 가 빈 문자열이라는 현재 계약에 의존. noisy entity-card 가족의 progress summary 정책이 바뀌면 본 어서션도 함께 조정되어야 함.
- `verification_label == "설명형 다중 출처 합의"` 는 multi-source agreement 분기의 라벨 규약에 의존. 라벨 문자열이 바뀌면 본 어서션과 기존 `first/second response_origin` verification_label 어서션이 함께 깨지도록 설계되어 있음.
- 본 라운드의 첫 응답 단계 어서션과 CONTROL_SEQ 59 의 reload 단계 어서션은 같은 두 테스트 안에서 서로 다른 단계를 덮음. 어느 한 단계에서 service 직렬화가 drift 하면 해당 단계 어서션이 먼저 깨져 drift 범위를 식별할 수 있음.
- 신규 어서션은 `first["session"]["web_search_history"][0]` 의 첫 entry 를 조회함. 두 테스트 모두 첫 호출 직후 session 의 history 에 entry 하나만 존재함을 전제함. 향후 첫 호출 시점에 entry 가 여러 개 생성되도록 흐름이 바뀌면 index 전제를 재검토해야 함.
- CONTROL_SEQ 56 (entity-card non-noisy initial-render browser × 2) → 57 (noisy initial-render browser × 1) → 58 (noisy show-only reload browser tightening × 1) → 59 (noisy 직접 reload service × 2) → 본 CONTROL_SEQ 60 (noisy 첫 응답 service × 2) 루프는 noisy entity-card strong-plus-missing 분기를 browser initial-render / browser reload-only / service direct reload / service initial response 네 축에서 truth-synced 로 잠그는 진행 패턴.
- 본 라운드는 commit / push / PR / branch publish / next slice 선택 을 수행하지 않음. handoff 지시대로 한 슬라이스 종료 후 즉시 stop.
