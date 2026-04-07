# entity-card dual-probe natural-reload response-origin truth-sync tightening

## 변경 파일
- `e2e/tests/web-smoke.spec.mjs`
- `README.md`
- `docs/ACCEPTANCE_CRITERIA.md`
- `docs/MILESTONES.md`
- `docs/TASK_BACKLOG.md`

## 사용 skill
- 없음 (기존 fixture/assertion/wording truth-sync)

## 변경 이유
- dual-probe natural-reload browser smoke의 pre-seeded record가 `verification_label: "설명형 단일 출처"`, `source_roles: ["백과 기반"]`을 사용하고 있었으나, 현재 런타임은 `설명형 다중 출처 합의`, `["공식 기반", "백과 기반"]`을 emit
- 문서도 동일한 outdated single-source wording을 남기고 있었음

## 핵심 변경
1. **브라우저 smoke (exact-field)**: scenario 42 — pre-seeded record, history item, assertion의 `verification_label`을 `설명형 다중 출처 합의`로, `source_roles`를 `["공식 기반", "백과 기반"]`로 변경, `공식 기반` assertion 추가
2. **브라우저 smoke (follow-up)**: scenario 44 — 동일 패턴으로 pre-seeded record, history item, assertion truth-sync
3. **docs**: scenario count 변경 없이 wording sync (README 2곳, ACCEPTANCE_CRITERIA 2곳, MILESTONES 2곳, TASK_BACKLOG 2곳)

## 검증
- `python3 -m unittest -v ...dual_probe_entity_search_natural_reload_exact_fields ...dual_probe_natural_reload_follow_up_preserves_response_origin` → 2 tests OK (0.096s)
- `cd e2e && npx playwright test ... -g "entity-card dual-probe 자연어 reload에서 response origin badge와 answer-mode badge가 유지됩니다"` → 1 passed (6.9s)
- `cd e2e && npx playwright test ... -g "entity-card dual-probe 자연어 reload 후 follow-up에서 response origin badge와 answer-mode badge가 drift하지 않습니다"` → 1 passed (6.6s)
- `git diff --check` → whitespace error 없음

## 남은 리스크
- dual-probe natural-reload response-origin truth-sync는 exact-field + follow-up 모두 닫힘
- history-card dual-probe source-path scenarios의 response-origin fixture completeness는 별도 슬라이스 필요 시 추가
