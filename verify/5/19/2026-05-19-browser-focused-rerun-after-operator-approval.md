STATUS: verified

# 2026-05-19 browser focused rerun after operator approval 검증

## 대상

- operator approval source: 채팅 응답 `승인`
- previous operator request: `.pipeline/operator_request.md` `CONTROL_SEQ: 1936`
- latest work source: `work/5/19/2026-05-19-browser-focused-rerun-test-stabilization.md`
- dirty source/test bundle:
  - `controller/js/cozy.js`
  - `e2e/tests/web-smoke.spec.mjs`
  - `tests/test_controller_server.py`

## 변경 파일

- `verify/5/19/2026-05-19-browser-focused-rerun-after-operator-approval.md`
- `.pipeline/operator_request.md`

## 결론

- operator가 socket-capable browser verification surface 사용을 승인했고, focused controller/browser rerun을 실제 실행했습니다.
- controller focused smoke는 통과했습니다.
- web-smoke focused rerun은 첫 실행에서 2개 test expectation/API drift를 잡았고, `e2e/tests/web-smoke.spec.mjs` 수정 뒤 같은 focused 묶음이 통과했습니다.
- 따라서 기존 `local_safe_work_exhausted_browser_verification_gate`의 focused browser verification blocker는 해소됐습니다.
- publication은 계속 held 상태입니다. commit, push, branch/PR publication, PR creation/reuse, merge, release, external publication은 실행하지 않았습니다.

## 실행한 검증

- PASS: `cd e2e && npx playwright test -c playwright.controller.config.mjs -g "controller shows active verify owner as working even when lane snapshot is ready" --reporter=line`
  - `1 passed (4.2s)`
- FAIL then fixed: `cd e2e && npx playwright test tests/web-smoke.spec.mjs -g "브라우저 폴더 선택으로도 문서 검색|검색만 응답|내용 거절은 approval|preference auto activation|reviewed-memory loop: 활성화된 선호" --reporter=line`
  - 첫 실행은 `3 passed`, `2 failed`였습니다.
  - 실패 test:
    - `내용 거절은 approval을 유지하고 나중 explicit save로 supersede 됩니다`
    - `preference auto activation notice appears in PreferencePanel after correction`
- PASS: `node --check e2e/tests/web-smoke.spec.mjs`
- PASS: `cd e2e && npx playwright test tests/web-smoke.spec.mjs -g "브라우저 폴더 선택으로도 문서 검색|검색만 응답|내용 거절은 approval|preference auto activation|reviewed-memory loop: 활성화된 선호" --reporter=line`
  - `5 passed (32.2s)`
- PASS: `git diff --check -- controller/js/cozy.js e2e/tests/web-smoke.spec.mjs tests/test_controller_server.py`

## 실행하지 않은 검증

- `make e2e-test`는 실행하지 않았습니다. 이번 operator approval은 focused controller/web-smoke rerun surface 제공으로 해석했고, release/full-smoke pass는 주장하지 않습니다.
- sqlite Playwright smoke, full controller smoke, broad unittest, long soak는 실행하지 않았습니다.
- `python3 -m unittest -v tests.test_controller_server tests.test_preference_injection tests.test_preference_handler`는 이번 round에서 새로 실행하지 않았습니다. 해당 non-socket pass는 2026-05-18 work/verify chain에 기록된 기존 evidence로만 남아 있습니다.

## 현재 truth

- focused browser verification blocker는 해소됐습니다.
- current dirty source/test bundle은 `controller/js/cozy.js`, `e2e/tests/web-smoke.spec.mjs`, `tests/test_controller_server.py`입니다.
- 이번 round에서 추가로 `work/5/19/2026-05-19-browser-focused-rerun-test-stabilization.md`, `verify/5/19/2026-05-19-browser-focused-rerun-after-operator-approval.md`, `.pipeline/operator_request.md`가 변경됐습니다.
- `.pipeline/operator_request.md`는 browser gate가 아니라, focused browser pass 이후 남은 publication-or-hold decision으로 갱신했습니다.
- publication은 held 상태입니다.

## 남은 리스크

- full `make e2e-test` pass가 없으므로 release-ready 또는 publication-ready로 볼 수 없습니다.
- broader controller smoke 전체가 아니라 active verify owner focused scenario만 재실행했습니다.
- 문서 변경은 하지 않았습니다. 이번 수정은 기존 test expectation 안정화이며, shipped product contract 변경은 아니라고 판단했습니다.
