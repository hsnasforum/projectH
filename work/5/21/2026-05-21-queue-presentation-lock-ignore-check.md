# 2026-05-21 Queue presentation lock ignore check

## 변경 파일

- `.gitignore`
- `work/5/21/2026-05-21-queue-presentation-lock-ignore-check.md`

## 사용 skill

- `work-log-closeout`: 실제 수정 여부, 재현 결과, 실행한 테스트, 남은 untracked 소스 상태를 한국어 `/work` 기록으로 남기기 위해 사용했습니다.

## 변경 이유

- 직전 verify에서 `controller/js/queue-presentation.js`와 `controller/js/state.js` 사이 ESM/CommonJS import mismatch로 `tests.test_controller_queue_presentation` 실패가 보고되었습니다.
- `.pipeline/.supervisor-start.lock`은 런타임 잠금 파일이므로 git status에 남지 않도록 `.gitignore`에 추가할 필요가 있었습니다.

## 핵심 변경

- `.gitignore`의 Pipeline runtime 섹션에 `.pipeline/.supervisor-start.lock`을 추가했습니다.
- `controller/js/queue-presentation.js`는 수정하지 않았습니다.
  - 실제 파일에는 ESM named import 구문이 없고 classic script 형태로 `globalThis.PipelineQueuePresentation`을 붙입니다.
  - `controller/js/state.js`는 현재 `import './queue-presentation.js';` 후 `export const PipelineState = new _PipelineState();`를 제공하므로, 직전 verify의 `Named export 'PipelineState' not found` 오류가 현재 워크트리에서는 재현되지 않았습니다.
- lock 파일은 `git status --short -- .pipeline/.supervisor-start.lock` 범위에서 더 이상 표시되지 않는 것을 확인했습니다.

## 검증

- 사전 확인:
  - `sed -n '1,240p' verify/5/21/2026-05-21-post-commit-untracked-triage.md`
  - 결과: `.pipeline/.supervisor-start.lock` ignore 필요, `queue-presentation.js` 테스트 실패 기록을 확인했습니다.
- 코드 확인:
  - `sed -n '1,220p' controller/js/queue-presentation.js`
  - `sed -n '1,220p' controller/js/state.js`
  - `rg -n "queue-presentation|PipelineState|Named export|state.js|import .*state" tests/test_controller_queue_presentation.py controller/js/queue-presentation.js controller/js/state.js controller/js/cozy.js controller/index.html`
  - 결과: `queue-presentation.js`에는 import가 없고, `state.js`가 `PipelineState`를 named export하는 현재 상태를 확인했습니다.
- targeted queue presentation 테스트:
  - `python3 -m unittest tests.test_controller_queue_presentation -v`
  - 결과: `Ran 3 tests in 0.113s` / `OK`.
- untracked source 묶음 테스트:
  - `python3 -m unittest tests.test_local_socket_guard tests.test_pipeline_runtime_state_contract tests.test_controller_queue_presentation -v`
  - 결과: `Ran 18 tests in 1.246s` / `OK`.
- whitespace 확인:
  - `git diff --check -- controller/js/queue-presentation.js .gitignore`
  - 결과: PASS. 출력 없음.
- ignore 확인:
  - `rg -n "supervisor-start" .gitignore`
  - 결과: `.gitignore:57:.pipeline/.supervisor-start.lock`.
  - `git status --short -- .gitignore .pipeline/.supervisor-start.lock controller/js/queue-presentation.js tests/test_controller_queue_presentation.py tests/test_local_socket_guard.py tests/test_pipeline_runtime_state_contract.py pipeline_runtime/state_contract.py tests/local_socket_guard.py tests/fixtures`
  - 결과: `.pipeline/.supervisor-start.lock`은 표시되지 않고, `.gitignore` 수정과 untracked 소스/테스트/fixture만 표시되었습니다.

## 남은 리스크

- `controller/js/queue-presentation.js` 자체는 아직 untracked입니다. 테스트는 통과했지만 commit 전 `git add controller/js/queue-presentation.js`가 필요합니다.
- `pipeline_runtime/state_contract.py`, `tests/local_socket_guard.py`, `tests/test_*`, `tests/fixtures/` 등 untracked 소스/테스트 파일도 아직 커밋되지 않았습니다.
- 직전 verify의 named import 오류는 현재 워크트리에서 재현되지 않아 별도 JS import 변경은 하지 않았습니다.
- commit, push, PR, merge, publish, Playwright, live runtime은 수행하지 않았습니다.
