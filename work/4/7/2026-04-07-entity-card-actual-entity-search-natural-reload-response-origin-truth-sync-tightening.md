# entity-card actual-entity-search natural-reload response-origin truth-sync tightening

## 변경 파일
- `tests/test_web_app.py`
- `e2e/tests/web-smoke.spec.mjs`
- `README.md`
- `docs/ACCEPTANCE_CRITERIA.md`
- `docs/MILESTONES.md`
- `docs/TASK_BACKLOG.md`

## 사용 skill
- 없음 (기존 테스트 fixture/assertion truth-sync)

## 변경 이유
- actual-search natural-reload의 exact-field와 follow-up response-origin 테스트가 one-result fixture를 사용하여 `설명형 단일 출처`를 잠그고 있었으나, 현재 런타임은 two-result fixture에서 `설명형 다중 출처 합의`를 emit
- 서비스/브라우저/문서가 런타임 truth와 어긋나는 mismatch를 해소하는 truth-sync tightening

## 핵심 변경
1. **서비스 테스트 (exact-field)**: `test_handle_chat_actual_entity_search_natural_reload_exact_fields` — fixture를 two-result로 확장 (verification_label이 `설명형 다중 출처 합의`로 자동 변경)
2. **서비스 테스트 (follow-up origin)**: `test_handle_chat_actual_entity_search_natural_reload_follow_up_preserves_response_origin` — fixture를 two-result로 확장
3. **브라우저 smoke (show-only)**: scenario 40 — pre-seeded record와 assertion의 verification_label을 `설명형 다중 출처 합의`로 변경
4. **브라우저 smoke (follow-up)**: scenario 45 — pre-seeded record를 two-result로 확장, verification_label을 `설명형 다중 출처 합의`로 변경
5. **docs**: scenario count 변경 없이 wording sync (README 2곳, ACCEPTANCE_CRITERIA 2곳, MILESTONES 2곳, TASK_BACKLOG 1곳)

## 검증
- `python3 -m unittest -v ...natural_reload_exact_fields ...natural_reload_follow_up_preserves_response_origin` → 2 tests OK (0.085s)
- `cd e2e && npx playwright test ... -g "entity-card 붉은사막 검색 결과 자연어 reload에서 response origin badge와 answer-mode badge가 유지됩니다"` → 1 passed (6.9s)
- `cd e2e && npx playwright test ... -g "entity-card 붉은사막 자연어 reload 후 follow-up에서 response origin badge와 answer-mode badge가 drift하지 않습니다"` → 1 passed (6.5s)
- `git diff --check` → whitespace error 없음

## 남은 리스크
- dual-probe/zero-strong-slot의 verification_label은 `설명형 단일 출처`가 맞으므로 이 슬라이스 범위 밖
- history-card click-reload family의 truth-sync는 별도 슬라이스 필요 시 추가
