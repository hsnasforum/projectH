STATUS: verified
CONTROL_SEQ: 155
BASED_ON_WORK: work/4/25/2026-04-25-m31-reviewed-memory-loop-e2e-smoke.md
VERIFIED_BY: Claude
NEXT_CONTROL: .pipeline/advisory_request.md CONTROL_SEQ 155 (M32 direction)

---

## M31 Axis 2: reviewed-memory loop E2E smoke test

### Verdict

PASS. 새 시나리오 1개가 `e2e/tests/web-smoke.spec.mjs` 끝에 추가됐고 전체 suite **147 passed (6.6m)** 확인.

implement 작업 노트의 `make e2e-test` 실패는 코드 문제가 아닌 인프라 이슈(포트 8879 이미 점유 → Makefile pre-start 충돌)였음. 기존 서버 재사용(`reuseExistingServer: true`)으로 직접 실행 시 정상 통과.

### Checks Run

- `git diff --check -- e2e/tests/web-smoke.spec.mjs` → exit 0
- `node --check e2e/tests/web-smoke.spec.mjs` → exit 0 (syntax OK)
- `cd e2e && npx playwright test tests/web-smoke.spec.mjs -g "reviewed-memory loop" --reporter=line` → **1 passed (5.4s)**
- `cd e2e && npm test` (기존 서버 재사용) → **147 passed (6.6m)**, exit 0

### Implementation Review

work 노트 기술과 일치:
- 시나리오 위치: `e2e/tests/web-smoke.spec.mjs:11969`
- 제목: `reviewed-memory loop: sync 후 활성화하면 이후 채팅 응답에 선호 반영 prefix가 붙습니다`
- 구현 방식: 실 데이터 경로
  - `createQualityReviewQueueItem()` → 실제 correction + candidate 생성
  - `/api/candidate-review` POST → preference candidate 수락 (real backend)
  - `/api/preferences/audit`, `/api/corrections/sync-adopted-to-candidates` → `page.route()` 모킹 (sync UI 검증용)
  - `/api/preferences/activate` POST → 실 backend activation (`page.request.post`)
  - 채팅 전송 → `[모의 응답, 선호 1건 반영]` prefix 실 mock adapter 검증 (`model_adapter/mock.py:24`)
- 기존 146개 시나리오 로직 변경 없음

### M31 Full Summary

| Axis | 내용 | 상태 |
|---|---|---|
| Axis 1 (SEQ 148–151) | release gate (146 E2E, 216 unit, e2e spawn fix) | ✓ |
| Axis 2 (SEQ 154–155) | reviewed-memory loop E2E smoke (147 passed) | ✓ |

### Next

M31 Axes 1–2 완료. M32 방향이 필요 — advisory 요청.
