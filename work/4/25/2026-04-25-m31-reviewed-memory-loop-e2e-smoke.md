# 2026-04-25 M31 reviewed-memory loop E2E smoke

## 변경 파일
- `e2e/tests/web-smoke.spec.mjs`
- `work/4/25/2026-04-25-m31-reviewed-memory-loop-e2e-smoke.md`

## 사용 skill
- `e2e-smoke-triage`: Playwright smoke 시나리오 추가 범위와 검증 순서를 좁게 유지하기 위해 사용했습니다.
- `work-log-closeout`: 구현 결과, 실제 실행한 검증, 남은 리스크를 `/work`에 기록하기 위해 사용했습니다.

## 변경 이유
- M31 Axis 2 handoff에 따라 reviewed-memory loop에서 sync 버튼 클릭, preference 활성화, 이후 채팅 응답의 active preference prefix 반영을 검증하는 Playwright 시나리오 1개를 추가했습니다.

## 핵심 변경
- 최종 시나리오 제목: `reviewed-memory loop: sync 후 활성화하면 이후 채팅 응답에 선호 반영 prefix가 붙습니다`
- 구현 접근: 원안 변형입니다. 실제 backend preference 후보는 기존 correction -> candidate confirmation -> candidate review accept 경로로 생성하고, sync 버튼 노출/상태는 기존 `page.route()` 패턴으로 `audit`/`sync` API를 모킹했습니다.
- `POST /api/preferences/activate`는 실제 backend endpoint를 호출해 생성된 preference를 `active`로 전환하도록 했습니다.
- React `app-preview`에서 provider를 `mock`으로 바꾼 뒤 채팅 입력/전송 UI를 사용하고, 응답에 `[모의 응답, 선호 1건 반영]` prefix와 `선호 1건 반영` 표시가 보이는지 확인합니다.
- 기존 시나리오 로직은 변경하지 않고 파일 끝에 새 `test(...)` 1개를 추가했습니다.

## 검증
- `git diff --check -- e2e/tests/web-smoke.spec.mjs`
  - 통과, 출력 없음.
- `node --check e2e/tests/web-smoke.spec.mjs`
  - 통과, 출력 없음.
- `cd e2e && npx playwright test tests/web-smoke.spec.mjs -g "reviewed-memory loop" --list`
  - 통과: `Total: 1 test in 1 file`
- `set -o pipefail; make e2e-test 2>&1 | tail -5`
  - 실패: Playwright `config.webServer` 시작 중 `PermissionError: [Errno 1] Operation not permitted`
  - `147 passed`는 확인하지 못했습니다. 서버 socket 생성 단계에서 중단되어 새 시나리오 본문은 런타임 실행되지 않았습니다.
- `rg -c '^test\(' e2e/tests/web-smoke.spec.mjs`
  - `131` 출력. 이 파일 기준 `test(` 카운트는 이번 변경으로 1개 증가했습니다.

## 남은 리스크
- 현재 샌드박스에서는 로컬 webServer socket 생성이 막혀 전체 `make e2e-test` 게이트를 완료할 수 없습니다.
- 새 시나리오는 문법 및 Playwright 등록까지만 확인되었고, 실제 브라우저 플로우 실행 결과는 별도 socket 허용 환경에서 재검증해야 합니다.
