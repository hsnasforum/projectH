# 2026-05-20 controller no queued task surface

## 변경 파일

- `controller/js/cozy.js`
- `controller/js/state.js`
- `controller/js/sidebar.js`
- `tests/test_controller_server.py`
- `work/5/20/2026-05-20-controller-no-queued-task-surface.md`

## 사용 skill

- `finalize-lite`: 구현 라운드 종료 전 검증 사실, 문서 동기화 필요성, 남은 리스크를 점검하기 위해 사용했습니다.
- `work-log-closeout`: 변경 파일, 실제 실행한 검사, 남은 리스크를 한국어 `/work` 기록으로 남기기 위해 사용했습니다.

## 변경 이유

- `.pipeline`에 active control slot이 없고 runtime이 정상 idle인 상태가 controller에서 `READY` lane과 `prompt_visible` note만으로 보이면, 실행 실패나 stuck handoff처럼 오해될 수 있었습니다.
- 이번 handoff의 목표는 정상 idle / no active control 상태를 stuck 또는 pending dispatch 상태와 화면에서 분리하는 것입니다.

## 핵심 변경

- controller presentation helper에 `isNoQueuedPipelineTask()`와 `pipelineQueuePresentation()`을 추가했습니다.
- `active_control_status == "none"`, control file/seq 없음, `active_round == null`, `automation_health == "ok"`인 live 상태를 `No queued pipeline task`로 표시하도록 했습니다.
- Cozy controller sidebar의 `Current Round` 섹션과 marquee에 `Queue` 행/문구를 추가했습니다.
- 모듈 원본인 `controller/js/state.js` / `controller/js/sidebar.js`에도 같은 presentation surface를 맞췄습니다.
- controller asset smoke 성격의 서버 테스트가 새 표시 문구와 helper 이름을 확인하도록 보강했습니다.

## 검증

- `python3 -m py_compile tests/test_controller_server.py`
  - 결과: PASS.
- `python3 -m unittest -v tests.test_controller_server.ControllerServerLaunchGateTests.test_controller_html_polls_runtime_api_only`
  - 결과: PASS.
- `node --check controller/js/cozy.js`
  - 결과: PASS.
- `git diff --check -- controller/js/state.js controller/js/sidebar.js controller/js/cozy.js tests/test_controller_server.py`
  - 결과: PASS.
- `node --input-type=module --check controller/js/state.js`
  - 결과: FAIL. Node가 `--input-type`을 파일 경로와 함께 받지 않아 검사 형식 오류가 났습니다.
- `node --input-type=module --check controller/js/sidebar.js`
  - 결과: FAIL. 같은 Node 검사 형식 오류입니다.
- `node --input-type=module --check < controller/js/state.js`
  - 결과: PASS.
- `node --input-type=module --check < controller/js/sidebar.js`
  - 결과: PASS.
- `python3 -m unittest -v tests.test_controller_server`
  - 결과: PASS. 28개 테스트가 모두 통과했습니다.

## 남은 리스크

- Playwright/e2e, 전체 unittest, long soak, socket-bound smoke는 실행하지 않았습니다. 이번 변경은 controller status presentation의 좁은 표시 변경입니다.
- 제품 문서는 수정하지 않았습니다. 이번 변경은 shipped contract 확장보다 controller 내부 상태 문구 보강에 가깝다고 판단했습니다.
- worktree에는 이번 라운드 이전부터 있던 다른 dirty 변경과 미추적 `/work`·`/verify` 파일들이 남아 있습니다. 이번 라운드는 위 변경 파일만 다뤘습니다.
- commit, push, PR, merge, release는 실행하지 않았습니다.
