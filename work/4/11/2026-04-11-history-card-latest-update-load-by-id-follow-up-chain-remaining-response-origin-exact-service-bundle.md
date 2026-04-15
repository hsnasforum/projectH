# history-card latest-update load-by-id follow-up-chain remaining response-origin exact service bundle

## 변경 파일

- `tests/test_web_app.py`

## 사용 skill

- 없음

## 변경 이유

직전 `/work` (`2026-04-11-history-card-latest-update-natural-reload-follow-up-chain-remaining-response-origin-exact-service-bundle.md`)와 대응 `/verify` (`verify/4/11/2026-04-11-history-card-latest-update-natural-reload-follow-up-chain-remaining-response-origin-verification.md`)는 baseline natural reload 경로의 first / second follow-up 체인 여섯 테스트에서 follow-up 응답 `origin`을 `provider`, `badge`, `label`, `kind`, `model`, `answer_mode`, variant별 `verification_label` / `source_roles`까지 exact-field로 고정했습니다. 즉, natural-reload follow-up chain은 이미 end-to-end로 닫힌 상태입니다.

같은 family에서 남은 가장 가까운 current-risk는 click reload / `load_web_search_record_id` follow-up chain이었습니다. 여섯 테스트 (mixed-source / single-source / news-only 각각의 first + second follow-up)는 follow-up 응답의 `origin`을 잡는 방식이 제각각이었습니다:

- mixed first follow-up: `answer_mode` / `verification_label` / `source_roles`만 고정
- mixed second follow-up: `badge` / `answer_mode` / `verification_label` / `source_roles`만 고정
- single first follow-up: `origin` assertion 아예 없음, `source_paths`만 검증
- single second follow-up: `badge` / `answer_mode` / `verification_label` / `source_roles`만 고정
- news-only first follow-up: `origin` assertion 아예 없음, `source_paths`만 검증
- news-only second follow-up: `badge` / `answer_mode` / `verification_label` / `source_roles`만 고정

노이즈-커뮤니티 latest-update 계열을 손대는 것보다 non-noisy click-reload 쪽이 더 단순한 shipped history-card user flow이고, first / second follow-up은 한 바운드 안에서 여섯 테스트를 함께 닫는 것이 micro-split 대비 자연스러운 단위이므로, 이 슬라이스는 여섯 테스트의 follow-up 응답 `origin` assertion을 latest-update exact-field 계약으로 한 번에 정렬합니다. stored-record 계약은 이미 앞선 라운드에서 잠겼으므로 이 라운드에서 stored-record assertion은 새로 추가하지 않았습니다.

## 핵심 변경

`tests/test_web_app.py`의 아래 여섯 click-reload follow-up 테스트에서, follow-up `handle_chat` 호출 직후의 `origin = <response>["response_origin"]` 블록을 latest-update exact-field 계약으로 강화했습니다 (single / news first follow-up은 기존에 `origin` assertion이 없었기 때문에 신규 블록을 추가했습니다). 기존 `source_paths` 검증, `history_entry` 조회, zero-count `claim_coverage_summary` / 빈 `claim_coverage_progress_summary` assertion 블록은 그대로 유지했습니다.

- `test_handle_chat_latest_update_mixed_source_follow_up_preserves_source_paths`  
  → session `"latest-mixed-followup-sp-session"`, first follow-up (`followup_origin = second["response"]["response_origin"]`)
- `test_handle_chat_latest_update_mixed_source_reload_second_follow_up_preserves_response_origin_and_source_paths`  
  → session `"latest-mixed-2fu-session"`, second follow-up (`origin = fourth[...]`)
- `test_handle_chat_latest_update_single_source_follow_up_preserves_source_paths`  
  → session `"latest-single-followup-sp-session"`, first follow-up (신규 `followup_origin` 블록 추가)
- `test_handle_chat_latest_update_single_source_reload_second_follow_up_preserves_response_origin_and_source_paths`  
  → session `"latest-single-2fu-session"`, second follow-up (`origin = fourth[...]`)
- `test_handle_chat_latest_update_news_only_follow_up_preserves_source_paths`  
  → session `"latest-news-followup-sp-session"`, first follow-up (신규 `followup_origin` 블록 추가)
- `test_handle_chat_latest_update_news_only_reload_second_follow_up_preserves_response_origin_and_source_paths`  
  → session `"latest-news-2fu-session"`, second follow-up (`origin = fourth[...]`)

여섯 테스트 공통 origin assertion 블록 (variant별 마지막 두 줄만 상이):

```
self.assertEqual(<origin>["provider"], "web")
self.assertEqual(<origin>["badge"], "WEB")
self.assertEqual(<origin>["label"], "외부 웹 최신 확인")
self.assertEqual(<origin>["kind"], "assistant")
self.assertIsNone(<origin>["model"])
self.assertEqual(<origin>["answer_mode"], "latest_update")
```

variant별 유지 라인:
- mixed-source: `verification_label == "공식+기사 교차 확인"`, `source_roles == ["보조 기사", "공식 기반"]`
- single-source: `verification_label == "단일 출처 참고"`, `source_roles == ["보조 출처"]`
- news-only: `verification_label == "기사 교차 확인"`, `source_roles == ["보조 기사"]`

natural-reload 쪽 테스트, by-id latest-update 쪽 다른 family, noisy-community latest-update family, entity-card / dual-probe / zero-strong / actual-search family, 브라우저/Playwright는 건드리지 않았습니다. stored-record assertion은 이번 라운드에서 새로 추가하지 않았습니다.

## 검증

- `python3 -m unittest -v tests.test_web_app.WebAppServiceTest.test_handle_chat_latest_update_mixed_source_follow_up_preserves_source_paths tests.test_web_app.WebAppServiceTest.test_handle_chat_latest_update_mixed_source_reload_second_follow_up_preserves_response_origin_and_source_paths tests.test_web_app.WebAppServiceTest.test_handle_chat_latest_update_single_source_follow_up_preserves_source_paths tests.test_web_app.WebAppServiceTest.test_handle_chat_latest_update_single_source_reload_second_follow_up_preserves_response_origin_and_source_paths tests.test_web_app.WebAppServiceTest.test_handle_chat_latest_update_news_only_follow_up_preserves_source_paths tests.test_web_app.WebAppServiceTest.test_handle_chat_latest_update_news_only_reload_second_follow_up_preserves_response_origin_and_source_paths` → `Ran 6 tests in 0.160s OK`
- `git diff --check -- tests/test_web_app.py work/4/11` → whitespace 경고 없음
- 이 슬라이스는 follow-up response surface service-only 대조이고 browser-visible 계약을 건드리지 않으므로 `make e2e-test`는 과합니다. targeted six-test bundle로 충분합니다.

## 남은 리스크

- noisy-community latest-update family (baseline / click-reload / follow-up / second follow-up / stored record / by-id 등) 계약은 이 슬라이스 범위 밖입니다.
- 이 라운드는 click-reload follow-up chain만 닫았고, entity-card 외 다른 family (dual-probe / zero-strong / actual-search) follow-up chain의 exact 계약은 확인하지 않았습니다.
- 저장소는 여전히 dirty 상태입니다 (`verify/4/10/...`, `verify/4/11/...`, 기존 `work/4/11/` 항목). 이 슬라이스는 그 pending 파일들을 되돌리거나 커밋하지 않았습니다.
