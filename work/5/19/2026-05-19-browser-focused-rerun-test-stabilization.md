# 2026-05-19 browser focused rerun test stabilization

## 변경 파일

- `e2e/tests/web-smoke.spec.mjs`
- `work/5/19/2026-05-19-browser-focused-rerun-test-stabilization.md`
- `verify/5/19/2026-05-19-browser-focused-rerun-after-operator-approval.md`
- `.pipeline/operator_request.md`

## 사용 skill

- `e2e-smoke-triage`: operator 승인 뒤 controller/web-smoke focused Playwright 재실행 범위를 좁히는 데 사용했습니다.
- `finalize-lite`: 의미 있는 테스트 수정 뒤 검증 정직성, doc-sync 필요성, `/work` closeout 필요성을 점검하는 데 사용했습니다.
- `release-check`: 실행한 check와 실행하지 않은 full gate를 분리해 readiness claim을 제한하는 데 사용했습니다.
- `doc-sync`: 이번 변경이 기존 시나리오 expectation 안정화인지, 제품/시나리오 문서 갱신이 필요한 contract 변경인지 판단하는 데 사용했습니다.
- `work-log-closeout`: 이번 변경과 실제 검증 결과를 표준 `/work` 형식으로 남기는 데 사용했습니다.
- `round-handoff`: operator 승인 뒤 browser verification truth를 `/verify`와 다음 control 경계로 정리하는 데 사용했습니다.

## 변경 이유

- `CONTROL_SEQ: 1936` operator stop은 socket-capable browser verification surface 제공 여부를 요구했고, 사용자가 채팅에서 `승인`을 명시했습니다.
- focused controller smoke는 통과했지만, focused web-smoke 재실행에서 기존 test expectation drift 두 건이 실제 실패로 확인됐습니다.
- source behavior를 바꾸지 않고 `web-smoke.spec.mjs`의 brittle expectation/API 사용만 좁게 수정해 pending browser verification gate를 해소했습니다.
- publication 승인은 별도로 주어지지 않았으므로 commit, push, branch/PR publication, PR creation/reuse, merge, release는 계속 held 상태로 유지했습니다.

## 핵심 변경

- approval preview expectation은 `[모의 요약]`과 `[모의 요약, 선호 N건 반영]` prefix를 모두 허용하는 기존 helper를 재사용하고, 실제 DOM text가 보존하지 않는 끝 공백 의존성을 제거했습니다.
- React preview correction flow의 edit textarea 선택은 Playwright에 없는 `page.getByDisplayValue()` 대신 `main textarea:not([placeholder])` locator로 변경했습니다.
- preference activation click은 기존 전역 `활성화` 버튼 locator 대신 해당 `#pref-card-${preferenceId}` 내부 버튼으로 좁혀 ambiguity를 줄였습니다.
- `.pipeline/operator_request.md`는 browser gate 미완료 상태를 더 이상 주장하지 않고, focused browser rerun 통과 뒤 남은 publication-or-hold 경계로 갱신했습니다.

## 검증

- PASS: `cd e2e && npx playwright test -c playwright.controller.config.mjs -g "controller shows active verify owner as working even when lane snapshot is ready" --reporter=line`
  - `1 passed (4.2s)`
- FAIL then fixed: `cd e2e && npx playwright test tests/web-smoke.spec.mjs -g "브라우저 폴더 선택으로도 문서 검색|검색만 응답|내용 거절은 approval|preference auto activation|reviewed-memory loop: 활성화된 선호" --reporter=line`
  - 첫 실행은 `3 passed`, `2 failed`였습니다.
  - 실패 원인은 approval preview 끝 공백 expectation과 Playwright에 없는 `page.getByDisplayValue()` API 사용이었습니다.
- PASS: `node --check e2e/tests/web-smoke.spec.mjs`
- PASS: `cd e2e && npx playwright test tests/web-smoke.spec.mjs -g "브라우저 폴더 선택으로도 문서 검색|검색만 응답|내용 거절은 approval|preference auto activation|reviewed-memory loop: 활성화된 선호" --reporter=line`
  - `5 passed (32.2s)`
- PASS: `git diff --check -- controller/js/cozy.js e2e/tests/web-smoke.spec.mjs tests/test_controller_server.py`

## 남은 리스크

- `make e2e-test`, sqlite smoke, full controller smoke, broad unittest, long soak는 실행하지 않았습니다. 이번 승인은 focused controller/web-smoke rerun에 한정해 해석했습니다.
- 이번 round는 full-smoke pass, release-ready, publication-ready를 주장하지 않습니다.
- publication은 계속 held 상태입니다. commit, push, branch/PR publication, PR creation/reuse, merge, release, external publication은 실행하지 않았습니다.
- docs는 갱신하지 않았습니다. 이번 수정은 기존 Playwright 시나리오의 expectation 안정화이며, 제품/시나리오 수를 바꾸는 shipped contract 변경은 아니라고 판단했습니다.
