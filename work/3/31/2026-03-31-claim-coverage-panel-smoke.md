# 2026-03-31 claim-coverage panel dedicated browser smoke

## 변경 파일
- `e2e/tests/web-smoke.spec.mjs`
- `README.md`
- `docs/ACCEPTANCE_CRITERIA.md`
- `docs/MILESTONES.md`
- `docs/TASK_BACKLOG.md`
- `docs/NEXT_STEPS.md`

## 사용 skill
- 없음

## 변경 이유
- claim-coverage panel은 이미 shipped user-visible surface이지만, mock adapter가 claim_coverage 데이터를 생성하지 않아 dedicated browser smoke가 없었음.
- latest verify에서 이 gap이 리스크로 남아 있었고, metadata docs sync 축과 별개의 현재 MVP risk reduction임.

## 핵심 변경

### smoke test 추가 (scenario 14)
- `page.evaluate`로 `renderClaimCoverage`를 deterministic claim_coverage 데이터(교차 확인 1, 단일 출처 1, 미확인 1)와 함께 직접 호출하여 순수 frontend rendering contract를 검증.
- 새 broad fixture나 web investigation mock 없이 가장 작은 deterministic path로 해결.
- 검증 항목:
  - `[교차 확인] 출생일` leading status tag
  - `[단일 출처] 소속` leading status tag
  - `[미확인] 수상 이력` leading status tag
  - `단일 출처` 행동 힌트: "1개 출처만 확인됨. 교차 검증이 권장됩니다."
  - `미확인` 행동 힌트: "추가 출처가 필요합니다."
  - panel hint: "교차 확인은 여러 출처 합의", "단일 출처는 신뢰 가능한 1개 출처 기준", "미확인은 추가 조사 필요 상태입니다"

### docs truth-sync
- smoke scenario count 13→14 반영: README, ACCEPTANCE_CRITERIA, MILESTONES, TASK_BACKLOG, NEXT_STEPS

## 검증
- `make e2e-test`: 14 passed (전체 통과)
- `git diff --check`: whitespace 오류 없음

## 남은 리스크
- 이 smoke는 frontend rendering contract만 보호함. backend가 claim_coverage를 올바르게 생성하는지는 별도 unit/integration test로 보호되어야 함.
- web investigation end-to-end flow에서 claim_coverage가 실제로 패널에 도달하는 경로는 mock 한계로 아직 browser smoke에서 직접 커버되지 않음.
