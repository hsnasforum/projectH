# 2026-04-25 M37 preference resume/reject E2E

## 변경 파일
- `e2e/tests/web-smoke.spec.mjs`
- `work/4/25/2026-04-25-m37-preference-resume-reject-e2e.md`

## 사용 skill
- `e2e-smoke-triage`: Playwright smoke 시나리오 추가와 selector/count 실패 원인을 좁혀 확인했습니다.
- `finalize-lite`: 최종 변경 파일, 검증 결과, doc-sync 필요 여부, 남은 리스크를 정리했습니다.
- `work-log-closeout`: 구현 closeout 형식과 실제 실행 결과 기록 기준을 맞췄습니다.

## 변경 이유
- `CONTROL_SEQ: 207` handoff에 따라 reviewed-memory preference lifecycle의 pause 이후 resume/reject 경로를 E2E로 닫아야 했습니다.
- 기존 scenario 148은 pause 및 pause persistence까지만 다루므로, 새 scenario 149에서 resume, reject, reject persistence를 count 기반으로 검증해야 했습니다.

## 핵심 변경
- `web-smoke.spec.mjs` 파일 끝에 `reviewed-memory loop: resume/reject lifecycle은 count 기반으로 검증됩니다` 시나리오를 추가했습니다.
- 새 시나리오는 candidate 생성, `/api/candidate-review` accept, `/api/preferences/activate` 활성화, badge popover pause, API 상태 poll, resume, reject를 한 흐름에서 확인합니다.
- seeded 또는 이전 Playwright 실행에서 남은 활성 preference가 10개 cap을 채워 count 감소를 가리는 경우를 피하려고, 시나리오 시작 시 Playwright가 만든 기존 active preference만 pause합니다.
- 동일 문구의 이전 실패 실행 응답을 잘못 집지 않도록 message token을 붙이고, 현재 mock 응답 paragraph를 기준으로 badge/popover locator를 스코프했습니다.
- scenario 148 및 앱/backend/frontend 코드는 수정하지 않았습니다.

## 검증
- `git diff --check -- e2e/tests/web-smoke.spec.mjs`
  - 통과, 출력 없음.
- `cd e2e && npx playwright test tests/web-smoke.spec.mjs -g 'resume.*reject|resume/reject' --reporter=line`
  - 최종 통과.
  - `1 passed (17.7s)`
- `make e2e-test`
  - 실패.
  - 최종 결과: `147 passed (13.9m)`, `2 failed`.
  - 실패 1: `tests/web-smoke.spec.mjs:11969:1` 기존 scenario 147이 `[모의 응답, 선호 1건 반영]`을 찾지 못했습니다.
  - 실패 2: `tests/web-smoke.spec.mjs:12071:1` 기존 scenario 148이 `선호 9건 반영`을 찾지 못했습니다.
  - 새 scenario 149는 전체 실행 안에서 통과했습니다: `reviewed-memory loop: resume/reject lifecycle은 count 기반으로 검증됩니다 (12.8s)`.

## 남은 리스크
- 전체 E2E gate는 green이 아닙니다. 실패는 이번 handoff에서 수정 금지된 기존 scenario 147/148의 count 가정에서 발생했습니다.
- 실패 컨텍스트는 `e2e/test-results/web-smoke-reviewed-memory--9bb3f-후-채팅-응답에-선호-반영-prefix가-붙습니다/error-context.md`와 `e2e/test-results/web-smoke-reviewed-memory--4968a-pover가-열리고-선호를-일시중지할-수-있습니다/error-context.md`에 남았습니다.
- 테스트 전부터 있던 `verify/4/25/2026-04-25-m36-preference-pause-functional-e2e.md` 변경과 `report/gemini/**` untracked 파일들은 이번 handoff 범위 밖이라 건드리지 않았습니다.
- commit, push, branch/PR 생성, 다음 slice 선택은 수행하지 않았습니다.
