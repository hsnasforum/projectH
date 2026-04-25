# 2026-04-24 operator attention board

## 변경 파일
- `controller/index.html`
- `controller/css/office.css`
- `controller/js/cozy.js`
- `e2e/tests/controller-smoke.spec.mjs`
- `tests/test_controller_server.py`
- `README.md`
- `docs/PRODUCT_SPEC.md`
- `docs/ACCEPTANCE_CRITERIA.md`
- `docs/TASK_BACKLOG.md`
- `work/4/24/2026-04-24-operator-attention-board.md`

## 사용 skill
- `frontend-skill`: controller Office View의 메인 작업면에 operator 알림판을 얹는 UI 변경이어서, 화면 위계와 작동 표면을 좁게 잡기 위해 사용했습니다.
- `doc-sync`: internal/operator tooling 동작과 controller smoke coverage가 바뀌어 README와 제품 문서의 현재 구현 설명을 맞추기 위해 사용했습니다.
- `work-log-closeout`: 실제 변경 파일, 실행한 검증, 남은 리스크를 `/work` closeout으로 남기기 위해 사용했습니다.

## 변경 이유
- `needs_operator`가 호출되어도 사용자가 왜 멈췄는지 메인 화면에서 알기 어렵다는 문제가 있었습니다.
- 사이드바의 Incident Room은 상세 상태에 가깝기 때문에, Office View의 오른쪽 빈 작업면에 현재 stop 이유와 다음 행동을 바로 보이는 operator attention board로 노출하는 작은 UI slice를 진행했습니다.

## 핵심 변경
- `controller/index.html`의 canvas 영역 안에 `#operator-attention-board` DOM shell을 추가했습니다.
- `controller/css/office.css`에 pixel parchment 스타일의 operator attention board를 추가하고, auth stop과 reason metadata missing 상태를 구분하는 시각 상태를 만들었습니다.
- `controller/js/cozy.js`에 `buildOperatorAttention` / `renderOperatorAttentionBoard`를 추가해 active `needs_operator` 또는 `automation_health=needs_operator`에서 reason label, reason_code, 대상 lane/role, `DECISION_REQUIRED`, control 파일/seq, evidence, next action을 표시하도록 했습니다.
- reason metadata가 없으면 `개입 필요 사유 누락`으로 표시해 stop 생성 경로의 reason contract drift가 숨지 않게 했습니다.
- 보드의 lane 버튼은 기존 bounded log modal을 재사용해 해당 lane terminal tail/input으로 이동합니다.
- controller smoke에 auth login `needs_operator` payload를 stub한 메인 보드 회귀 테스트를 추가했고, 관련 source-presence 단위 테스트와 문서를 동기화했습니다.

## 검증
- `node --check controller/js/cozy.js`
  - 통과: 출력 없음
- `python3 -m py_compile controller/server.py tests/test_controller_server.py`
  - 통과: 출력 없음
- `git diff --check -- controller/index.html controller/css/office.css controller/js/cozy.js tests/test_controller_server.py e2e/tests/controller-smoke.spec.mjs`
  - 통과: 출력 없음
- `python3 -m unittest -v tests.test_controller_server`
  - 통과: `Ran 27 tests`, `OK`
- `cd e2e && npx playwright test tests/controller-smoke.spec.mjs -g "operator attention board" --reporter=line`
  - 통과: `1 passed`
- `cd e2e && npx playwright test tests/controller-smoke.spec.mjs --reporter=line`
  - 통과: `16 passed`
- `git diff --check -- README.md docs/PRODUCT_SPEC.md docs/ACCEPTANCE_CRITERIA.md docs/TASK_BACKLOG.md controller/index.html controller/css/office.css controller/js/cozy.js tests/test_controller_server.py e2e/tests/controller-smoke.spec.mjs`
  - 통과: 출력 없음
- `python3 -m unittest -v tests.test_docs_sync`
  - 통과: `Ran 13 tests`, `OK`

## 남은 리스크
- 이번 변경은 controller 표시 표면을 보강한 것이며, `needs_operator` 생성 경로 자체가 항상 `reason_code`/`DECISION_REQUIRED`를 쓰도록 강제하는 backend schema 변경은 아닙니다. 누락 시 보드가 `개입 필요 사유 누락`을 표시하지만, 실제 emit 경로 보강은 별도 slice가 필요합니다.
- 인증/OAuth/API key 계열은 reason 문자열 기반 label로 분류합니다. 더 정확한 분류가 필요하면 runtime status payload에 `reason_label`, `blocking_lane`, `safe_user_action`, `evidence_summary` 같은 구조화 필드를 표준화해야 합니다.
- 작업 시작 전 이미 controller/runtime 관련 dirty 파일이 많았고, 이번 closeout은 그중 operator attention board에 직접 손댄 파일과 문서 동기화만 기록합니다.
