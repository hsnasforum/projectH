# history-card entity-card actual-search smoke-doc truth-sync tightening

## 변경 파일
- `README.md`
- `docs/ACCEPTANCE_CRITERIA.md`
- `docs/MILESTONES.md`

## 사용 skill
- 없음 (docs-only truth-sync)

## 변경 이유
- 직전 round에서 scenarios 48/49에 response-origin continuity assertion이 추가되었으나, 문서(README, ACCEPTANCE_CRITERIA, MILESTONES)는 아직 source-path plurality만 기술하고 있었음
- current smoke coverage가 실제로 잠그는 `WEB` badge, `설명 카드`, `설명형 다중 출처 합의`, `백과 기반` continuity를 문서에 반영

## 핵심 변경
1. **README.md**: scenarios 48/49 설명에 source-path + response-origin continuity 반영
2. **docs/ACCEPTANCE_CRITERIA.md**: 동일 scenarios의 acceptance bullet에 response-origin continuity 반영
3. **docs/MILESTONES.md**: 동일 milestones bullet에 response-origin continuity 반영

## 검증
- `rg` cross-check → scenarios 48/49에 `설명형 다중 출처 합의`, `백과 기반` 반영 확인
- `git diff --check` → whitespace error 없음
- docs-only slice이므로 Python/Playwright 재실행 생략; latest `/verify` 결과(`verify/4/7/2026-04-07-entity-card-actual-search-response-origin-continuity-tightening-verification.md`)를 근거로 문서만 sync

## 남은 리스크
- docs truth-sync 완료; scenarios 48/49는 source-path + response-origin 모두 닫힘
- zero-strong-slot family, latest-update family의 truth-sync는 별도 슬라이스 필요 시 추가
