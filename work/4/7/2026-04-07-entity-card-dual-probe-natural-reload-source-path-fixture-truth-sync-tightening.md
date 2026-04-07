# entity-card dual-probe natural-reload source-path fixture truth-sync tightening

## 변경 파일
- `e2e/tests/web-smoke.spec.mjs`

## 사용 skill
- 없음 (기존 fixture truth-sync)

## 변경 이유
- dual-probe natural-reload source-path scenarios (41, 43)의 pre-seeded record가 `verification_label: "설명형 단일 출처"`, `source_roles: ["백과 기반"]`을 사용하고 있었으나, 런타임 truth는 `설명형 다중 출처 합의`, `["공식 기반", "백과 기반"]`
- source-path continuity assertion은 그대로 유지하면서 stale impossible record만 제거

## 핵심 변경
1. **scenario 41** (show-only source-path): pre-seeded record와 history item의 `verification_label`을 `설명형 다중 출처 합의`로, `source_roles`를 `["공식 기반", "백과 기반"]`로 변경
2. **scenario 43** (follow-up source-path): 동일 패턴으로 fixture truth-sync

## 검증
- `python3 -m unittest -v ...dual_probe_entity_search_natural_reload_exact_fields ...dual_probe_natural_reload_follow_up_preserves_response_origin` → 2 tests OK (0.118s)
- `cd e2e && npx playwright test ... -g "entity-card dual-probe 자연어 reload에서 source path가 context box에 유지됩니다"` → 1 passed (7.4s)
- `cd e2e && npx playwright test ... -g "entity-card dual-probe 자연어 reload 후 follow-up에서 source path가 context box에 유지됩니다"` → 1 passed (7.0s)
- `git diff --check` → whitespace error 없음

## 남은 리스크
- dual-probe natural-reload family의 fixture truth-sync는 response-origin + source-path 모두 닫힘
- history-card dual-probe family의 stale fixture는 별도 슬라이스 필요 시 추가
