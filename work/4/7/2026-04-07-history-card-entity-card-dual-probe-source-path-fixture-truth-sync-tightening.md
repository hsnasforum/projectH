# history-card entity-card dual-probe source-path fixture truth-sync tightening

## 변경 파일
- `tests/test_web_app.py`
- `e2e/tests/web-smoke.spec.mjs`

## 사용 skill
- 없음 (기존 stored-record/pre-seeded fixture truth-sync)

## 변경 이유
- history-card dual-probe source-path scenarios (23/31)의 서비스 `store.save` fixture와 브라우저 pre-seeded record가 `verification_label: "설명형 단일 출처"`, `source_roles: ["백과 기반"]`을 사용하고 있었으나, 런타임 truth는 `설명형 다중 출처 합의`, `["공식 기반", "백과 기반"]`
- source-path assertion은 그대로 유지하면서 stale impossible record만 제거

## 핵심 변경
1. **서비스 (show-only reload)**: `test_handle_chat_entity_card_dual_probe_reload_preserves_active_context_source_paths` — `store.save` fixture의 `response_origin` truth-sync
2. **서비스 (follow-up)**: `test_handle_chat_entity_card_dual_probe_follow_up_preserves_source_paths` — `store.save` fixture의 `response_origin` truth-sync
3. **브라우저 (scenario 23)**: pre-seeded record와 history item의 `verification_label`/`source_roles` truth-sync
4. **브라우저 (scenario 31)**: 동일 패턴으로 fixture truth-sync

## 검증
- `python3 -m unittest -v ...dual_probe_reload_preserves_active_context_source_paths ...dual_probe_follow_up_preserves_source_paths` → 2 tests OK (0.037s)
- `python3 -m unittest -v ...dual_probe_entity_search_history_card_reload_exact_fields` → OK (0.059s)
- `cd e2e && npx playwright test ... -g "history-card entity-card 다시 불러오기 후 dual-probe source path가 context box에 유지됩니다"` → 1 passed (7.4s)
- `cd e2e && npx playwright test ... -g "history-card entity-card 다시 불러오기 후 follow-up 질문에서 dual-probe source path가 context box에 유지됩니다"` → 1 passed (6.9s)
- `git diff --check` → whitespace error 없음

## 남은 리스크
- history-card dual-probe family의 fixture truth-sync는 source-path + response-origin 모두 닫힘
- zero-strong-slot family, latest-update family의 stale fixture는 별도 슬라이스 필요 시 추가
