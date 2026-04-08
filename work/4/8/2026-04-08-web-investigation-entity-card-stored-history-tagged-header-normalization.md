# Web Investigation entity-card stored-history tagged-header normalization

## 변경 파일

- `core/agent_loop.py`
- `tests/test_web_app.py`
- `e2e/tests/web-smoke.spec.mjs`

## 사용 skill

- 없음

## 변경 이유

새로 생성되는 web investigation 응답은 tagged section header (`확인된 사실 [교차 확인]:` 등)를 사용하지만, 기존 저장된 entity-card history record를 reload할 때는 `record["summary_text"]`를 그대로 재사용하여 legacy untagged header (`확인된 사실:`)가 브라우저에 노출됐음. `docs/PRODUCT_SPEC.md`가 tagged header를 구현 완료로 기술하고 있어, stored-history reload 경로와의 불일치가 사용자 visible inconsistency였음.

## 핵심 변경

### core/agent_loop.py
1. `_normalize_legacy_summary_headers` static method 추가: reload 시점에 legacy untagged header를 현재 tagged contract로 정규화
   - `확인된 사실:` → `확인된 사실 [교차 확인]:`
   - `단일 출처 정보 (교차 확인 부족, 추가 확인 필요):` → `단일 출처 정보 [단일 출처] (추가 확인 필요):`
   - `단일 출처 정보 (교차 확인 필요):` → `단일 출처 정보 [단일 출처] (추가 확인 필요):`
   - `확인되지 않은 항목:` → `확인되지 않은 항목 [미확인]:`
2. stored entity-card reload 경로에서 `stored_summary_text`를 verbatim 사용하는 대신 `_normalize_legacy_summary_headers` 적용
3. 디스크 상 stored JSON은 변경하지 않음 — render time only normalization

### tests/test_web_app.py
- `test_handle_chat_entity_card_reload_preserves_stored_summary_text`: verbatim 보존 assertion에서 정규화된 tagged header 포함 확인으로 변경

### e2e/tests/web-smoke.spec.mjs
- 3개 시나리오 (click reload, natural reload follow-up, natural reload second follow-up)에서 `확인된 사실:` + `교차 확인` 분리 assertion을 `확인된 사실 [교차 확인]:` 단일 assertion으로 변경
- fixture `summary_text`는 legacy 형식 유지 (정규화 동작 검증 목적)

## 검증

- `python3 -m unittest -v tests.test_web_app.WebAppServiceTest.test_handle_chat_entity_card_reload_preserves_stored_summary_text ...`: 5 tests OK
- Playwright `history-card entity-card 다시 불러오기 후 noisy single-source claim` 시나리오: 1 passed
- Playwright `entity-card noisy single-source claim 자연어 reload 후 follow-up` 시나리오: 1 passed
- `git diff --check`: whitespace 에러 없음

## 남은 리스크

- `docs/PRODUCT_SPEC.md:293`의 `clearer slot-level reinvestigation UX`는 별도 슬라이스로 남아 있음.
- latest-update 경로의 stored-history에도 같은 legacy header 문제가 있을 수 있으나, entity-card reload 경로만 이번 슬라이스 범위.
- 정규화는 알려진 legacy 패턴에 대해서만 동작하므로, 알 수 없는 변형이 있을 경우 미처리될 수 있음.
