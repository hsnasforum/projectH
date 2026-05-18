# 2026-04-26 pipeline launcher hibernate surface

## 변경 파일
- `pipeline-launcher.py`
- `controller/js/cozy.js`
- `controller/js/state.js`
- `tests/test_pipeline_launcher.py`
- `e2e/tests/controller-smoke.spec.mjs`
- `work/4/26/2026-04-26-pipeline-launcher-hibernate-surface.md`

## 사용 skill
- `work-log-closeout`: 구현 결과와 실제 검증 결과를 한국어 closeout으로 남겼다.

## 변경 이유
- 사용자가 M44 publish 흐름 대신 멈춰 있는 pipeline launcher 쪽 개발로 방향 전환을 요청했다.
- runtime canonical truth가 `control=none`, `automation_health=ok`인 non-operator `hibernate` 상태에서도 compat `operator_request.md`가 남아 있으면 런처/컨트롤러가 operator wait처럼 보일 수 있었다.
- 실제 approval/publication 경계는 계속 `needs_operator`로 보여야 하지만, `operator_eligible=false`인 내부 대기 상태는 큰 개입 카드가 아니라 자동 대기 상태로 보여야 한다.

## 핵심 변경
- `pipeline-launcher.py`가 `autonomy.reason_code`, `operator_policy`, `decision_class`, `operator_eligible`을 읽어 hibernate 상태를 `비운영자 자동 대기`로 표시하게 했다.
- 문자열 `"false"` 같은 status 값을 truthy로 오해하지 않도록 launcher에 `_truthy_flag`를 두었다.
- canonical control이 `none`인 경우 compat `operator_request.md`를 active control처럼 snapshot에 끌어올리지 않는 테스트를 추가했다.
- controller presentation의 같은 축 dirty 변경은 canonical `control=none`, `automation_health=ok`, `autonomy.mode=hibernate`, `operator_eligible=false` 조건에서만 suppressed debug를 내도록 좁혔다.
- canonical `needs_operator` control은 control status를 낮추지 않으므로 기존 real-risk operator wait 표시가 유지된다.

## 검증
- `python3 -m py_compile pipeline-launcher.py` 통과.
- `python3 -m unittest tests.test_pipeline_launcher -v` 통과: 32 tests.
- `cd e2e && npx playwright test tests/controller-smoke.spec.mjs -g "controller hides non-operator hibernate gate from operator attention board" --reporter=line` 실패: Playwright webServer가 `LocalOnlyHTTPServer` 소켓 생성 중 `PermissionError: [Errno 1] Operation not permitted`로 시작하지 못했다.
- `node --check controller/js/cozy.js` 통과.
- `node --check controller/js/state.js` 통과.
- `node --input-type=module -e "import { PipelineState } from './controller/js/state.js'; ..."` 통과: `needs_operator` control은 유지되고 canonical `none` hibernate만 `suppressedOperatorCandidate`가 된다.
- `git diff --check -- pipeline-launcher.py controller/js/cozy.js controller/js/state.js tests/test_pipeline_launcher.py e2e/tests/controller-smoke.spec.mjs` 통과.

## 남은 리스크
- controller Playwright smoke는 환경의 로컬 소켓 생성 제한으로 실행 완료하지 못했다. JS 문법 검사와 `PipelineState` 직접 확인으로 보완했지만 브라우저 렌더링 검증은 남아 있다.
- M44 publish gate는 사용자의 방향 전환에 따라 보류 상태이며 이번 구현에서 publish/merge하지 않았다.
- 기존 untracked `report/gemini/**`, 이전 `work/`/`verify/` 기록들은 이번 구현 범위 밖이라 정리하지 않았다.
