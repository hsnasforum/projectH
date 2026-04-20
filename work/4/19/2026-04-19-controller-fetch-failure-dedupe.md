# 2026-04-19 controller fetch failure dedupe

## 변경 파일
- `controller/js/cozy.js`
- `e2e/tests/controller-smoke.spec.mjs`
- `tests/test_controller_server.py`
- `README.md`
- `docs/PRODUCT_SPEC.md`
- `docs/ACCEPTANCE_CRITERIA.md`
- `docs/MILESTONES.md`
- `docs/TASK_BACKLOG.md`
- `work/4/19/2026-04-19-controller-fetch-failure-dedupe.md`

## 사용 skill
- `doc-sync`: controller Quest Log의 fetch-failure 계약 변경을 README / product docs / acceptance / milestone / backlog에 같은 사실로 맞추기 위해 사용.
- `work-log-closeout`: 이번 controller fetch-failure 정리 라운드의 `/work` closeout을 repo 규약 형식으로 남기기 위해 사용.

## 변경 이유
- controller 화면에서 `/api/runtime/status` fetch가 끊기면 `pollRuntime()`이 같은 `Failed to fetch`를 매 poll마다 Quest Log에 계속 쌓아, 실제 장애보다 로그 폭주가 더 크게 보였습니다.
- 현재 머신에는 `controller.server` 프로세스도 떠 있지 않아 screenshot의 network-level `Failed to fetch`가 실제로 재현 가능한 상태였습니다.
- 이번 라운드는 controller를 새로운 truth source로 키우지 않고, 같은 fetch 실패를 한 번만 기록하고 polling 복구 시 한 번만 복구 이벤트를 남기도록 좁게 정리했습니다.

## 핵심 변경
- `controller/js/cozy.js`에 `recordStatusFetchFailure()` / `clearStatusFetchFailure()`를 추가해 같은 상태 조회 실패 메시지는 1회만 Quest Log에 적재되게 했습니다.
- `pollRuntime()`이 `/api/runtime/status`의 non-OK 응답과 `data.ok === false`도 fetch failure 흐름으로 처리하고, 성공 복귀 시 `상태 조회 복구: ...`를 1회 남기도록 고정했습니다.
- `e2e/tests/controller-smoke.spec.mjs`에 repeated fetch abort 후 recovery 시나리오를 추가해, 동일 실패 중복 로그가 1건으로 유지되고 recovery 로그가 1건만 남는지 고정했습니다.
- `tests/test_controller_server.py`와 문서들에 새 controller Quest Log 계약과 controller smoke 범위를 반영했습니다.
- 로컬에서 `python3 -m controller.server`를 다시 백그라운드로 올리고 `http://127.0.0.1:8780/controller`가 200으로 응답하는 것까지 확인했습니다.

## 검증
- `python3 -m py_compile controller/server.py tests/test_controller_server.py`
  - 결과: 통과
- `python3 -m unittest -v tests.test_controller_server`
  - 결과: `Ran 23 tests`, `OK`
- `cd e2e && CONTROLLER_SMOKE_PORT=8782 npx playwright test -c playwright.controller.config.mjs --reporter=line`
  - 결과: `12 passed`
- `git diff --check -- controller/js/cozy.js e2e/tests/controller-smoke.spec.mjs tests/test_controller_server.py README.md docs/PRODUCT_SPEC.md docs/ACCEPTANCE_CRITERIA.md docs/MILESTONES.md docs/TASK_BACKLOG.md`
  - 결과: 출력 없음
- `nohup python3 -m controller.server > tmp/controller-server.log 2>&1 &`
  - 결과: controller server 재기동
- `curl -sS -o /dev/null -w '%{http_code}\n' http://127.0.0.1:8780/controller`
  - 결과: `200`
- `curl -sS -o /tmp/controller-status.json -w '%{http_code}\n' http://127.0.0.1:8780/api/runtime/status`
  - 결과: `200`
- `python3 - <<'PY' ... /tmp/controller-status.json ... PY`
  - 결과: `runtime_state=RUNNING`, `run_id=20260418T155014Z-p712989`

## 남은 리스크
- 이번 라운드는 controller fetch failure surface를 줄이는 데 집중했습니다. 현재 확인 시점에는 runtime도 `RUNNING`이지만, 이후 runtime이 다시 내려가면 controller는 더 이상 flood되지는 않아도 `runtime status not available` 계열 실패를 1회 기록한 채로 남습니다.
- `pipeline_runtime.cli daemon`의 현재 `RUNNING` 상태는 확인했지만, 이번 라운드의 핵심 수정은 controller Quest Log dedupe입니다. runtime lifecycle 자체의 재발 원인은 별도 runtime/watcher slice에서 계속 봐야 합니다.
- Quest Log dedupe는 동일 오류 메시지 기준입니다. 서로 다른 fetch 오류 메시지가 번갈아 나오면 각각 1회씩은 남습니다.
