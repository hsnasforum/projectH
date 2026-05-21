# 2026-05-21 Pipeline bugfix bundle smoke verification

## 변경 파일

- `work/5/21/2026-05-21-pipeline-bugfix-bundle-smoke-verification.md`

## 사용 skill

- `work-log-closeout`: 순수 검증 라운드의 실제 실행 명령, 실패/정체 지점, dirty diff 범위, 다음 판단을 한국어 `/work` 기록으로 남기기 위해 사용했습니다.

## 변경 이유

- P1-P18 pipeline launcher/runtime bugfix bundle과 runs 자동 정리 변경이 web app 레이어에 import/runtime 사이드 이펙트를 내는지 `tests.test_smoke`와 `tests.test_web_app`으로 확인하는 라운드였습니다.
- 이번 라운드는 코드, 테스트, 문서 수정 없이 검증과 기록만 수행하는 범위였습니다.

## 핵심 변경

- 코드 변경 없음.
- `verify/5/21/2026-05-21-pipeline-runs-dir-auto-cleanup.md`와 최신 `/work` 기록을 먼저 확인했습니다.
- 요청된 smoke 명령, 전체 tracked diff stat, pipeline_runtime 관련 whitespace check를 실행했습니다.
- smoke 명령이 완료되지 않아 commit 준비 완료로 판단하지 않았습니다.

## 검증

- 직전 verify 확인:
  - `sed -n '1,220p' verify/5/21/2026-05-21-pipeline-runs-dir-auto-cleanup.md`
  - 결과: runs cleanup 직전 verify는 `READY`, supervisor py_compile/unittest/diff-check 통과로 기록되어 있었습니다.
- 최신 `/work` 확인:
  - `sed -n '1,220p' work/5/21/2026-05-21-pipeline-runs-dir-auto-cleanup.md`
  - 결과: runs cleanup 구현 closeout을 확인했습니다.
- web app smoke 확인:
  - `python3 -m unittest tests.test_smoke tests.test_web_app -v`
  - 결과: PASS 아님. 약 4분 동안 진행 후 `tests.test_web_app.WebAppServiceTest.test_handle_chat_external_fact_colloquial_info_questions_use_web_search_when_enabled`에서 무출력 정체되어 `kill -INT`로 중단했습니다.
  - 중단 시 스택:
    - `tests/test_web_app.py:8981`
    - `app/handlers/chat.py`
    - `core/agent_loop.py`의 `_handle_external_fact_search` -> `_run_web_search` -> `_maybe_review_response`
    - `model_adapter/ollama.py`의 `review_draft` -> `_generate` -> `_iter_request_json_lines`
    - 최종 대기 지점: `http.client` / `socket.recv_into`에서 Ollama streaming response 대기
  - 해석: smoke/web_app 전체 통과를 확인하지 못했습니다. 마지막 정체는 pipeline_runtime import 단계가 아니라 web app의 live Ollama review path에서 발생했습니다.
- 실행 중 unittest 정리 확인:
  - `ps -o pid,ppid,stat,etime,cmd -u "$USER" | rg "python3 -m unittest tests.test_smoke tests.test_web_app|tests.test_web_app|tests.test_smoke" || true`
  - 결과: 남아 있는 해당 unittest 프로세스 없음.
- whitespace 확인:
  - `git diff --check -- pipeline_runtime/supervisor.py pipeline_runtime/cli.py pipeline_runtime/automation_health.py tests/test_pipeline_runtime_supervisor.py tests/test_pipeline_runtime_cli.py tests/test_pipeline_runtime_automation_health.py`
  - 결과: 통과했습니다.

### git diff --stat

```text
 .gitignore                                         |    1 +
 .pipeline/README.md                                |   18 +-
 README.md                                          |   23 +-
 app/handlers/reviewed_memory.py                    |   95 +-
 app/serializers.py                                 |    1 +
 app/static/app.js                                  |    7 +
 controller/index.html                              |    1 +
 controller/js/cozy.js                              |  111 +-
 controller/js/sidebar.js                           |    1 +
 controller/js/state.js                             |   66 +-
 controller/server.py                               |   21 +-
 docs/ACCEPTANCE_CRITERIA.md                        |   12 +-
 docs/ARCHITECTURE.md                               |    8 +-
 docs/MILESTONES.md                                 |    1 +
 docs/PRODUCT_SPEC.md                               |    7 +-
 docs/TASK_BACKLOG.md                               |    1 +
 ...63\204_\353\252\205\354\204\270\354\204\234.md" |   13 +-
 .../05_\354\232\264\354\230\201_RUNBOOK.md"        |    9 +-
 e2e/tests/controller-smoke.spec.mjs                |   78 +
 e2e/tests/web-smoke.spec.mjs                       |   11 +
 pipeline-launcher.py                               |  255 +++-
 pipeline_runtime/automation_health.py              |  101 +-
 pipeline_runtime/cli.py                            |  158 +-
 pipeline_runtime/operator_autonomy.py              |   11 +
 pipeline_runtime/supervisor.py                     |  399 +++--
 tests/test_controller_server.py                    |  713 ++++++++-
 tests/test_http_integration.py                     |   59 +-
 tests/test_pipeline_launcher.py                    |   72 +
 tests/test_pipeline_runtime_automation_health.py   |  263 +++-
 tests/test_pipeline_runtime_cli.py                 |  211 ++-
 tests/test_pipeline_runtime_control_writers.py     |   15 +
 tests/test_pipeline_runtime_supervisor.py          | 1615 +++++++++++++++++++-
 tests/test_smoke.py                                |    1 +
 tests/test_watcher_core.py                         |  801 +++++++++-
 tests/test_web_app.py                              |  482 ++++++
 verify_fsm.py                                      |   70 +-
 watcher_core.py                                    |    7 +-
 watcher_dispatch.py                                |  117 +-
 watcher_prompt_assembly.py                         |   12 +-
 39 files changed, 5238 insertions(+), 609 deletions(-)
```

## 남은 리스크

- `tests.test_smoke tests.test_web_app` 전체 통과를 확인하지 못했으므로 `commit 준비 완료`가 아닙니다.
- 다음 판단: `다음 수정 필요`. 별도 라운드에서 `test_handle_chat_external_fact_colloquial_info_questions_use_web_search_when_enabled`의 live Ollama review path 정체 원인을 분리하거나, 해당 smoke가 deterministic mock/timeout 경로를 쓰도록 정리한 뒤 재검증해야 합니다.
- `git diff --stat` 기준 tracked dirty 범위는 프롬프트의 pipeline_runtime 6개 파일보다 넓습니다. app/controller/docs/e2e/watcher 계열 변경도 tracked diff에 포함되어 있어, commit bundle 판단 전에 실제 포함 범위를 다시 확정해야 합니다.
- `git status --short` 기준 untracked `work/`, `verify/`, `tests/fixtures/`, `pipeline_runtime/state_contract.py`, `controller/js/queue-presentation.js` 등도 존재합니다. `git diff --stat`에는 untracked 파일이 포함되지 않으므로 publish/commit 전 별도 선별이 필요합니다.
- Playwright, E2E, live runtime start/stop, commit, push, PR, merge는 요청 범위 밖이라 수행하지 않았습니다.
