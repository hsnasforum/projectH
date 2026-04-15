# history-card latest-update noisy-community natural-reload remaining response-origin exact service bundle

## 변경 파일

- `tests/test_web_app.py`

## 사용 skill

- 없음

## 변경 이유

직전 `/work` (`2026-04-11-history-card-latest-update-noisy-community-click-reload-stored-record-remaining-response-origin-exact-service-bundle.md`)와 대응 `/verify` (`verify/4/11/2026-04-11-history-card-latest-update-noisy-community-click-reload-stored-record-remaining-response-origin-verification.md`)는 noisy-community latest-update click-reload 경로 (show-only reload / first follow-up / second follow-up) 세 테스트에서 surface `response_origin`과 persisted stored `response_origin` 두 층을 latest-update exact-field 계약으로 end-to-end 잠갔습니다. 즉, click-reload 쪽 noisy-community 경로는 이미 닫힌 상태입니다.

같은 noisy-community latest-update family에서 남은 가장 가까운 current-risk는 natural-reload 쪽 follow-up chain이었습니다. `test_handle_chat_latest_update_noisy_source_excluded_after_natural_reload_follow_up`과 `test_handle_chat_latest_update_noisy_source_excluded_after_natural_reload_second_follow_up` 두 테스트는 follow-up 응답 `origin`에서 `badge` / `answer_mode` / `verification_label` / `source_roles`만 exact로 잡고, `provider` / `label` / `kind` / `model`은 미고정, 그리고 `self.assertNotIn("보조 커뮤니티", ...)`, `self.assertNotIn("brunch", ...)` negative 제외 계약과 positive `source_paths`, zero-count claim_coverage 블록만 유지하고 있었습니다. 이 슬라이스는 stored-record 작업이나 다른 history-card family로 넘어가는 대신, 두 테스트의 surface `origin`만 click-reload 쪽과 동일한 latest-update exact-field 계약으로 정렬합니다.

## 핵심 변경

`tests/test_web_app.py`의 아래 두 service 테스트에서, follow-up `handle_chat` 호출 직후 `origin` 블록에 latest-update 전체 literal 세트 assertion을 추가했습니다. 기존 negative 제외 계약(`보조 커뮤니티`, `brunch`), positive retained `source_paths`, `latest_entry["verification_label"]` 확인 및 zero-count `claim_coverage_summary` / 빈 `claim_coverage_progress_summary` 블록은 그대로 유지했습니다.

- `test_handle_chat_latest_update_noisy_source_excluded_after_natural_reload_follow_up`  
  → session `"latest-noisy-nat-fu-session"`, first follow-up `origin` (`third[...]`)
- `test_handle_chat_latest_update_noisy_source_excluded_after_natural_reload_second_follow_up`  
  → session `"latest-noisy-nat-2fu-session"`, second follow-up `origin` (`fourth[...]`)

두 테스트 공통 origin assertion 블록:

```
self.assertEqual(origin["provider"], "web")
self.assertEqual(origin["badge"], "WEB")
self.assertEqual(origin["label"], "외부 웹 최신 확인")
self.assertEqual(origin["kind"], "assistant")
self.assertIsNone(origin["model"])
self.assertEqual(origin["answer_mode"], "latest_update")
self.assertEqual(origin["verification_label"], "기사 교차 확인")
self.assertEqual(origin["source_roles"], ["보조 기사"])
```

noisy-community click-reload 테스트, noisy-community natural-reload 쪽 stored-record 확인, non-noisy latest-update family, entity-card / dual-probe / zero-strong / actual-search family, 브라우저/Playwright는 건드리지 않았습니다.

## 검증

- `python3 -m unittest -v tests.test_web_app.WebAppServiceTest.test_handle_chat_latest_update_noisy_source_excluded_after_natural_reload_follow_up tests.test_web_app.WebAppServiceTest.test_handle_chat_latest_update_noisy_source_excluded_after_natural_reload_second_follow_up` → `Ran 2 tests in 0.075s OK`
- `git diff --check -- tests/test_web_app.py work/4/11` → whitespace 경고 없음
- 이 슬라이스는 follow-up response surface service-only 대조이고 browser-visible 계약을 건드리지 않으므로 `make e2e-test`는 과합니다. targeted two-test bundle로 충분합니다.

## 남은 리스크

- noisy-community natural-reload 쪽 persisted stored `response_origin` exact 계약 (store-read 기반)은 이 슬라이스 범위 밖으로 남겨 두었습니다.
- 같은 axis에서 entity-card 외 다른 family (dual-probe / zero-strong / actual-search)의 noisy natural-reload 경로 exact 계약은 이 라운드에서 확인하지 않았습니다.
- 저장소는 여전히 dirty 상태입니다 (`verify/4/10/...`, `verify/4/11/...`, 기존 `work/4/11/` 항목). 이 슬라이스는 그 pending 파일들을 되돌리거나 커밋하지 않았습니다.
