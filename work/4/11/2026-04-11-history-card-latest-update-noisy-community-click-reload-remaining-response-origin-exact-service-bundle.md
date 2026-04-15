# history-card latest-update noisy-community click-reload remaining response-origin exact service bundle

## 변경 파일

- `tests/test_web_app.py`

## 사용 skill

- 없음

## 변경 이유

직전 `/work` (`2026-04-11-history-card-latest-update-load-by-id-second-follow-up-stored-record-remaining-response-origin-exact-service-bundle.md`)와 대응 `/verify` (`verify/4/11/2026-04-11-history-card-latest-update-load-by-id-second-follow-up-stored-record-remaining-response-origin-verification.md`)는 non-noisy click-reload latest-update 경로를 show-only by-id, first follow-up surface + stored, second follow-up surface + stored까지 end-to-end로 잠갔습니다. 즉, non-noisy click-reload 경로는 이미 닫힌 상태입니다.

같은 history-card click-reload 흐름에서 남은 가장 가까운 current-risk는 noisy-community click-reload 세 테스트 (show-only reload / first follow-up / second follow-up)였습니다. 기존 상태는 다음과 같았습니다:

- show-only reload: `reload_origin`에서 `answer_mode`만 고정, `badge` / `label` / `provider` / `kind` / `model` / `verification_label` / 정확 positive `source_roles`는 모두 미고정
- first follow-up: `badge` / `answer_mode` / `verification_label` / `source_roles`만 고정
- second follow-up: `badge` / `answer_mode` / `verification_label` / `source_roles`만 고정

natural-reload noisy 계열이나 noisy stored-record 작업으로 넘어가는 대신, 같은 click-reload user flow 위에서 세 테스트를 하나의 일관된 바운드로 묶어 non-noisy click-reload 경로와 동일한 latest-update exact-field surface 계약으로 정렬하는 편이 same-family current-risk reduction에 더 직접적이라고 판단했습니다. negative 제외 계약(`보조 커뮤니티`, `brunch`)과 positive retained `source_paths`, zero-count `claim_coverage_summary` / 빈 `claim_coverage_progress_summary` assertion은 그대로 유지했습니다.

## 핵심 변경

`tests/test_web_app.py`의 아래 세 service 테스트에서, noisy-community 계열 reload / follow-up surface의 `origin` assertion을 non-noisy click-reload 경로와 동일한 latest-update exact-field 계약으로 강화했습니다.

- `test_handle_chat_latest_update_noisy_source_excluded_after_history_card_reload`  
  → session `"latest-update-noisy-reload-by-id-session"`, show-only `reload_origin` (`second["response"]["response_origin"]`) 쪽 강화
- `test_handle_chat_latest_update_noisy_source_excluded_after_history_card_reload_follow_up`  
  → session `"latest-noisy-click-fu-session"`, first follow-up `origin` (`third[...]`) 쪽 강화
- `test_handle_chat_latest_update_noisy_source_excluded_after_history_card_reload_second_follow_up`  
  → session `"latest-noisy-click-2fu-session"`, second follow-up `origin` (`fourth[...]`) 쪽 강화

세 테스트 공통 origin literal 블록:

```
self.assertEqual(<origin>["provider"], "web")
self.assertEqual(<origin>["badge"], "WEB")
self.assertEqual(<origin>["label"], "외부 웹 최신 확인")
self.assertEqual(<origin>["kind"], "assistant")
self.assertIsNone(<origin>["model"])
self.assertEqual(<origin>["answer_mode"], "latest_update")
self.assertEqual(<origin>["verification_label"], "기사 교차 확인")
self.assertEqual(<origin>["source_roles"], ["보조 기사"])
```

기존 negative 제외 계약(`self.assertNotIn("보조 커뮤니티", str(origin["source_roles"]))`, `self.assertNotIn("brunch", ...)`), positive retained `source_paths` (`hankyung`, `mk.co.kr` 포함 / `brunch` 미포함), zero-count `claim_coverage_summary` / 빈 `claim_coverage_progress_summary` 블록은 전부 그대로 유지했습니다.

non-noisy latest-update family, natural-reload noisy 테스트, noisy stored-record 검사, entity-card 계열 noisy 테스트, 브라우저/Playwright는 건드리지 않았습니다.

## 검증

- `python3 -m unittest -v tests.test_web_app.WebAppServiceTest.test_handle_chat_latest_update_noisy_source_excluded_after_history_card_reload tests.test_web_app.WebAppServiceTest.test_handle_chat_latest_update_noisy_source_excluded_after_history_card_reload_follow_up tests.test_web_app.WebAppServiceTest.test_handle_chat_latest_update_noisy_source_excluded_after_history_card_reload_second_follow_up` → `Ran 3 tests in 0.082s OK`
- `git diff --check -- tests/test_web_app.py work/4/11` → whitespace 경고 없음
- 이 슬라이스는 follow-up/reload response surface service-only 대조이고 browser-visible 계약을 건드리지 않으므로 `make e2e-test`는 과합니다. targeted three-test bundle로 충분합니다.

## 남은 리스크

- noisy-community latest-update 쪽의 natural-reload 경로(`test_handle_chat_latest_update_noisy_source_excluded_after_natural_reload_follow_up` 등)와 persisted stored-record `response_origin` exact 계약은 이 슬라이스 범위 밖입니다.
- entity-card family 외 다른 family (dual-probe / zero-strong / actual-search)의 noisy click-reload 경로 exact 계약은 이 라운드에서 확인하지 않았습니다.
- 저장소는 여전히 dirty 상태입니다 (`verify/4/10/...`, `verify/4/11/...`, 기존 `work/4/11/` 항목). 이 슬라이스는 그 pending 파일들을 되돌리거나 커밋하지 않았습니다.
