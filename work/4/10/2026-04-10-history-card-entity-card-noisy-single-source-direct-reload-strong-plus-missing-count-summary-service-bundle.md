# history-card entity-card noisy single-source direct-reload strong-plus-missing count-summary service bundle

## 변경 파일
- `tests/test_web_app.py` — 기존 noisy entity-card 직접 reload 서비스 테스트 두 개를 제자리에서 tighten:
  - `:11118` `test_handle_chat_entity_card_multi_source_agreement_retained_after_history_card_reload` (`load_web_search_record_id` show-only reload)
  - `:11252` `test_handle_chat_entity_card_multi_source_agreement_over_noise_natural_reload` (자연어 `"방금 검색한 결과 다시 보여줘"` reload)
  - 각 테스트의 기존 text / origin / noisy 제외 / source_paths provenance 어서션은 그대로 유지한 채, reload 이후 `second["session"]["web_search_history"][0]` 에 대해 reload 단계의 shipped history summary 계약을 직접 잠그는 어서션을 추가:
    - `verification_label == "설명형 다중 출처 합의"`
    - `claim_coverage_summary == {"strong": 3, "weak": 0, "missing": 2}`
    - `claim_coverage_progress_summary == ""`
- `e2e/tests/web-smoke.spec.mjs` 는 전혀 건드리지 않음 (handoff 가 browser 쪽을 범위 밖으로 명시). 기존 `:2615` 의 noisy entity-card show-only reload `.meta` 어서션 (CONTROL_SEQ 58) 과 `:2503` 의 initial-render 어서션 (CONTROL_SEQ 57) 이 그대로 잠겨 있음.

## 사용 skill
- `round-handoff`

## 변경 이유
- CONTROL_SEQ 58 (`2026-04-10-history-card-entity-card-noisy-single-source-reload-only-strong-plus-missing-meta-browser-tightening.md`) 가 noisy entity-card 의 **browser** show-only reload `.meta` 계약을 잠갔으므로, handoff 는 "Do not reopen that already-closed browser slice" 라고 명시하고 가장 인접한 same-family current-risk 로 **service 측 직접 reload 단계의 shipped count-summary dict / 빈 progress / verification_label** 을 지목함.
- 기존 `:11118` / `:11252` 직접 reload 테스트는 response text / response_origin exact fields / source_paths provenance / noisy 제외 계약은 잠갔지만, `session.web_search_history[0]` 의 shipped history summary shape 를 직접 어서션하지 않았음. 즉 reload 시점에 history card 가 받는 payload 가 `{strong:3, weak:0, missing:2}` + 빈 progress + `설명형 다중 출처 합의` 라는 계약이 service 쪽에서 지금까지는 post-follow-up 체인 (`:19532`, `:19687`) 에서만 간접적으로 증명되어 왔음.
- 브라우저는 CONTROL_SEQ 57/58 에서 pre-click initial-render + post-click show-only reload 의 `.meta` exact text 를 잠갔으므로, 같은 단계 (직접 reload) 의 service 직렬화가 동일 shape 를 내도록 본 라운드에서 service 직렬화 truth 를 browser truth 와 같은 지점에서 정합화함.
- `storage/web_search_store.py:316` + `app/serializers.py:280-287` 의 직렬화 경로는 `claim_coverage` 에서 `_summarize_claim_coverage` 를 통해 `{strong, weak, missing}` dict 를 만들고, 빈 progress 와 `설명형 다중 출처 합의` verification_label 을 함께 직렬화함. 본 라운드의 신규 어서션은 이 경로를 직접 reload 단계에서 exact 값으로 잠금.

## 핵심 변경
1. **`tests/test_web_app.py:11118` in-place tightening**
   - 기존 `second["session"]["active_context"]["source_paths"]` 어서션 뒤에 reload history summary 블록을 추가:
     - `reload_history = second["session"]["web_search_history"][0]`
     - `assertEqual(reload_history["verification_label"], "설명형 다중 출처 합의")`
     - `assertEqual(reload_history["claim_coverage_summary"], {"strong": 3, "weak": 0, "missing": 2})`
     - `assertEqual(reload_history["claim_coverage_progress_summary"], "")`
   - 설명형 주석으로 이 세 어서션이 reload 시점의 strong-plus-missing count-summary + 빈 progress + 설명형 다중 출처 합의 분기를 직접 잠금 의도임을 명시.
2. **`tests/test_web_app.py:11252` in-place tightening**
   - 자연어 reload (`"방금 검색한 결과 다시 보여줘"`) 이후 `source_paths` 어서션 뒤에 같은 세 어서션을 추가.
   - 설명형 주석으로 이 세 어서션이 자연어 reload 시점에 동일 계약을 잠금 의도임을 명시.
3. **범위 밖 유지**
   - `e2e/tests/web-smoke.spec.mjs`, latest-update, dual-probe, zero-count, docs, pipeline/config 는 전혀 건드리지 않음 (handoff 지시).
   - 기존 두 테스트의 다른 어서션 (strong slot 유지, `확인된 사실 [교차 확인]:` 본문, `출시일`/`2025`/`blog.example.com` 제외, response_origin exact fields, `source_paths` provenance) 은 그대로 유지.
   - 기존 helper / fixture / `_FakeWebSearchTool` seed / `record_id` 조회 패턴을 그대로 재사용하고 duplicate 테스트를 만들지 않음.

## 검증
이번 라운드 실행:
- `python3 -m unittest -v tests.test_web_app.WebAppServiceTest.test_handle_chat_entity_card_multi_source_agreement_retained_after_history_card_reload tests.test_web_app.WebAppServiceTest.test_handle_chat_entity_card_multi_source_agreement_over_noise_natural_reload` → 두 테스트 모두 `ok` (신규 history summary 어서션이 실제 runtime 에서 `{strong:3, weak:0, missing:2}` + 빈 progress + 설명형 다중 출처 합의 분기와 정확히 일치함을 확인)
- `git diff --check -- tests/test_web_app.py work/4/10` → 출력 없음 (공백 오류 없음)

이번 라운드에서 재실행하지 않음:
- `python3 -m unittest -v tests.test_web_app` 전체 슈트 — handoff 가 focused 두 service anchor 만 재실행을 요구했고, 본 슬라이스는 같은 두 테스트 안에서만 어서션을 확장함
- Playwright 스위트 또는 `make e2e-test` — browser 측은 건드리지 않았고 CONTROL_SEQ 57/58 이 noisy entity-card browser `.meta` 계약을 이미 잠가둠
- 기존 `:19532`, `:19687` 등 follow-up 체인 회귀 — 본 슬라이스는 직접 reload 단계만 targets 하므로 follow-up 체인을 다시 실행할 필요 없음

## 남은 리스크
- 신규 `claim_coverage_summary == {"strong": 3, "weak": 0, "missing": 2}` 어서션은 `_summarize_claim_coverage` 의 key 규약(`strong`/`weak`/`missing`) 과 값 타입(int) 에 의존. `CoverageStatus` StrEnum 이 dict equality 에서 plain string 과 같게 비교되므로 현재 runtime 에서 정확히 일치함. 향후 key 이름이나 타입이 바뀌면 본 어서션이 먼저 깨져 drift 를 가리킴.
- `claim_coverage_progress_summary == ""` 는 노이즈 제거된 strong-plus-missing 분포에서 progress summary 가 비어 있다는 현재 계약에 의존. noisy entity-card 가족의 progress summary 정책이 바뀌면 본 어서션도 함께 조정되어야 함.
- `verification_label == "설명형 다중 출처 합의"` 는 multi-source agreement 분기의 라벨 규약에 의존. 라벨 문자열이 바뀌면 본 어서션과 기존 `response_origin` verification_label 어서션이 함께 깨지도록 설계되어 있음.
- 본 라운드는 service 측 직접 reload 단계만 잠그며, follow-up / second follow-up 체인은 기존 `:19532`, `:19687` 가 이미 잠가둔 상태. 두 계층이 서로 다른 단계를 덮고 있어 어느 한쪽이 먼저 깨지면 나머지 한쪽도 drift 를 가리킬 수 있음.
- CONTROL_SEQ 56 (entity-card non-noisy initial-render × 2) → 57 (noisy initial-render browser × 1) → 58 (noisy show-only reload browser tightening × 1) → 본 CONTROL_SEQ 59 (noisy 직접 reload service × 2) 루프는 noisy entity-card strong-plus-missing 분기를 browser initial-render / browser reload-only / service direct reload 세 축에서 truth-synced 로 잠그는 진행 패턴.
- handoff 가 "service tests untouched unless a concrete mismatch" 가 아닌 "tighten only the two existing noisy entity-card direct reload service tests" 를 요구한 점에 유의. 본 라운드는 그 지시대로 duplicate 테스트를 만들지 않고 두 테스트의 끝 부분만 확장함.
- 신규 어서션은 `second["session"]["web_search_history"][0]` 의 첫 entry 를 조회함. 기존 테스트가 각 호출 후 session 의 history 에 한 개 entry 만 존재함을 전제하므로 (테스트 설계상 그렇게 되어 있음) index 조회로 충분. 향후 테스트 흐름에 history entry 가 여러 개 추가되면 index 전제를 재검토해야 함.
- 본 라운드는 commit / push / PR / branch publish / next slice 선택 을 수행하지 않음. handoff 지시대로 한 슬라이스 종료 후 즉시 stop.
