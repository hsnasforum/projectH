# history-card entity-card zero-strong-slot second-follow-up response-origin exact-web-badge service bundle verification

## 변경 파일
- `verify/4/10/2026-04-10-history-card-header-badge-count-plus-progress-claim-coverage-meta-smoke-tightening-verification.md`
- `.pipeline/claude_handoff.md`

## 사용 skill
- `round-handoff`

## 변경 이유
- 최신 `/work` 인 `work/4/10/2026-04-10-history-card-entity-card-zero-strong-slot-second-follow-up-response-origin-exact-web-badge-service-bundle.md` 가 실제 코드와 focused rerun 결과를 truthful 하게 설명하는지 다시 확인해야 했습니다.
- 이번 round 의 목적은 zero-strong second-follow-up 두 entry path 에 추가된 literal `response_origin` 어서션이 실제로 존재하는지 확인하고, `/work` 의 family-level closeout 및 residual-family 목록이 현재 코드와 맞는지 함께 재대조하는 것이었습니다.
- 지시된 범위대로 broader suite 나 Playwright rerun 으로 넓히지 않고, 최신 `/work` 가 직접 근거로 삼은 서비스 테스트 2건과 `git diff --check` 만 다시 실행했습니다.

## 핵심 변경
- 최신 `/work` 의 구현 설명과 focused rerun 자체는 현재 작업 트리 기준으로 truthful 합니다.
  - [tests/test_web_app.py#L18009](/home/xpdlqj/code/projectH/tests/test_web_app.py#L18009) 의 click-reload second-follow-up anchor 는 실제로 `badge == "WEB"`, `answer_mode == "entity_card"`, `verification_label == "설명형 단일 출처"`, `source_roles == ["백과 기반"]` literal exact 로 잠겨 있습니다.
  - [tests/test_web_app.py#L18218](/home/xpdlqj/code/projectH/tests/test_web_app.py#L18218) 의 natural-reload second-follow-up anchor 도 inline literal 블록으로 같은 네 어서션을 직접 추가했습니다.
  - `/work` 설명대로 shared helper `_assert_origin_and_sources` 본문은 그대로 유지됐고, natural second-follow-up 에만 후행 literal 블록을 덧붙이는 방식으로 범위를 좁게 지켰습니다.
- 최신 `/work` 의 검증 섹션도 truthful 합니다.
  - 지정된 unit command 를 다시 돌려 `Ran 2 tests in 0.108s - OK` 를 확인했습니다.
  - `git diff --check -- tests/test_web_app.py work/4/10 verify/4/10 .pipeline/claude_handoff.md` 역시 출력 없이 끝났습니다.
  - broader `tests.test_web_app` 전체와 Playwright 는 이번 round 에서 다시 돌리지 않았습니다. 변경 범위가 서비스 테스트 2건 안의 second-follow-up `response_origin` tightening 뿐이었기 때문입니다.
- 이번에는 `/work` 의 zero-strong family-level closeout 자체는 과장으로 보이지 않습니다.
  - reload-only 는 [tests/test_web_app.py#L10563](/home/xpdlqj/code/projectH/tests/test_web_app.py#L10563) / [tests/test_web_app.py#L10645](/home/xpdlqj/code/projectH/tests/test_web_app.py#L10645), first-follow-up 는 [tests/test_web_app.py#L17918](/home/xpdlqj/code/projectH/tests/test_web_app.py#L17918) / [tests/test_web_app.py#L18084](/home/xpdlqj/code/projectH/tests/test_web_app.py#L18084), second-follow-up 는 [tests/test_web_app.py#L18009](/home/xpdlqj/code/projectH/tests/test_web_app.py#L18009) / [tests/test_web_app.py#L18218](/home/xpdlqj/code/projectH/tests/test_web_app.py#L18218) 에서 now direct literal exact 로 잠겨 있습니다.
  - browser exact contract 도 이미 [e2e/tests/web-smoke.spec.mjs#L6053](/home/xpdlqj/code/projectH/e2e/tests/web-smoke.spec.mjs#L6053), [e2e/tests/web-smoke.spec.mjs#L6293](/home/xpdlqj/code/projectH/e2e/tests/web-smoke.spec.mjs#L6293), [e2e/tests/web-smoke.spec.mjs#L6410](/home/xpdlqj/code/projectH/e2e/tests/web-smoke.spec.mjs#L6410), [e2e/tests/web-smoke.spec.mjs#L6683](/home/xpdlqj/code/projectH/e2e/tests/web-smoke.spec.mjs#L6683), [e2e/tests/web-smoke.spec.mjs#L6791](/home/xpdlqj/code/projectH/e2e/tests/web-smoke.spec.mjs#L6791), [e2e/tests/web-smoke.spec.mjs#L6913](/home/xpdlqj/code/projectH/e2e/tests/web-smoke.spec.mjs#L6913) 에서 닫혀 있어 zero-strong reload chain closure 자체는 현재 코드와 모순되지 않습니다.
- 다만 최신 `/work` 의 residual-family 목록은 완전하지 않습니다.
  - `/work` 는 “남은 가족은 noisy entity-card / latest-update / store-seeded / general 등”이라고 적었지만, noisy entity-card 는 이미 [tests/test_web_app.py#L19563](/home/xpdlqj/code/projectH/tests/test_web_app.py#L19563), [tests/test_web_app.py#L19640](/home/xpdlqj/code/projectH/tests/test_web_app.py#L19640), [tests/test_web_app.py#L19718](/home/xpdlqj/code/projectH/tests/test_web_app.py#L19718), [tests/test_web_app.py#L19795](/home/xpdlqj/code/projectH/tests/test_web_app.py#L19795) 에서 four-field exactness 까지 이미 닫혀 있습니다.
  - 반대로 generic/simple entity-card service anchor 는 아직 loose 합니다. [tests/test_web_app.py#L16634](/home/xpdlqj/code/projectH/tests/test_web_app.py#L16634) 는 reload-only 를 `first_origin` baseline-derived equality 로만 보고, [tests/test_web_app.py#L16730](/home/xpdlqj/code/projectH/tests/test_web_app.py#L16730) 는 follow-up 에서 `assertIn(..., ("entity_card", first_origin["answer_mode"]))` 수준에 머뭅니다.
  - browser 는 이미 [e2e/tests/web-smoke.spec.mjs#L1379](/home/xpdlqj/code/projectH/e2e/tests/web-smoke.spec.mjs#L1379) / [e2e/tests/web-smoke.spec.mjs#L1645](/home/xpdlqj/code/projectH/e2e/tests/web-smoke.spec.mjs#L1645) 에서 simple entity-card reload-only / follow-up exact contract 를 잠그고 있으므로, residual current-risk 를 더 정확히 쓰면 generic/simple entity-card stored-origin service exactness 가 더 가깝습니다.

## 검증
- `python3 -m unittest -v tests.test_web_app.WebAppServiceTest.test_handle_chat_zero_strong_slot_entity_card_history_card_reload_second_follow_up_preserves_source_paths tests.test_web_app.WebAppServiceTest.test_handle_chat_zero_strong_slot_entity_card_natural_reload_second_follow_up_preserves_response_origin_and_source_paths` → `Ran 2 tests in 0.108s - OK`
- `git diff --check -- tests/test_web_app.py work/4/10 verify/4/10 .pipeline/claude_handoff.md` → 출력 없음
- next-slice 판정 보조 대조:
  - `sed -n '17990,18230p' tests/test_web_app.py`
  - `nl -ba tests/test_web_app.py | sed -n '18000,18215p'`
  - `sed -n '19550,19840p' tests/test_web_app.py`
  - `sed -n '16535,16745p' tests/test_web_app.py`
  - `nl -ba tests/test_web_app.py | sed -n '8598,8640p'`
  - `nl -ba tests/test_web_app.py | sed -n '16628,16736p'`
  - `nl -ba e2e/tests/web-smoke.spec.mjs | sed -n '1376,1398p'`
  - `nl -ba e2e/tests/web-smoke.spec.mjs | sed -n '1642,1665p'`
- broader `tests.test_web_app` 전체, isolated Playwright rerun, `make e2e-test` 는 재실행하지 않았습니다. 이번 round 는 서비스 테스트 2건의 truthful 여부 확인이 목적이었고, browser-visible contract 변경은 없었습니다.

## 남은 리스크
- zero-strong entity-card reload chain 은 이번 round 로 truthful 하게 닫혔습니다.
- 하지만 generic/simple entity-card stored-response-origin service 경계는 아직 browser exact contract 와 서비스 exact contract 사이에 작은 차이가 남아 있습니다.
- [tests/test_web_app.py#L16634](/home/xpdlqj/code/projectH/tests/test_web_app.py#L16634) 는 reload-only stage 를 baseline-derived equality 로만 보고, [tests/test_web_app.py#L16730](/home/xpdlqj/code/projectH/tests/test_web_app.py#L16730) 는 follow-up stage 에서 `response_origin` 존재와 loose `answer_mode` inclusion 만 확인합니다.
- browser exactness 는 이미 [e2e/tests/web-smoke.spec.mjs#L1379](/home/xpdlqj/code/projectH/e2e/tests/web-smoke.spec.mjs#L1379) / [e2e/tests/web-smoke.spec.mjs#L1645](/home/xpdlqj/code/projectH/e2e/tests/web-smoke.spec.mjs#L1645) 에서 닫혀 있으므로, next slice 는 simple entity-card reload-only + follow-up stored-response-origin exactness 를 함께 tighten 하는 bounded service bundle 하나면 충분합니다.
