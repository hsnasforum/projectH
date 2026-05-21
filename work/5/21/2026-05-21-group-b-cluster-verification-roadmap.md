# 2026-05-21 Group B cluster verification roadmap

## 변경 파일

- `work/5/21/2026-05-21-group-b-cluster-verification-roadmap.md`

## 사용 skill

- `work-log-closeout`: Group B 클러스터별 실제 검증 결과, 판정, operator용 커밋 순서 로드맵을 한국어 `/work` 기록으로 남기기 위해 사용했습니다.

## 변경 이유

- Group A는 직전 verify 기준으로 별도 커밋 가능한 상태였고, Group B tracked dirty 파일 33개는 문서, watcher/verify, app/controller/launcher, test/e2e 산출물이 섞여 있었습니다.
- operator가 커밋 순서를 결정할 수 있도록 각 클러스터의 최소 검증 결과와 커밋 준비 상태를 분리해 기록했습니다.

## 핵심 변경

- 코드 변경 없음.
- Group B 33개 파일을 사용자 지정 4개 클러스터로 분류해 검증했습니다.
- 클러스터 1~3은 요청된 diff/compile/unittest 검증을 통과해 `커밋 준비 완료`로 판정했습니다.
- 클러스터 4는 Python 테스트와 diff check는 통과했지만 e2e live server 검증을 실행하지 않았으므로 전체 판정은 `판정 불가`로 남겼습니다.
- commit, push, PR, merge, publish는 수행하지 않았습니다.

## 검증

### 사전 확인

- `sed -n '1,240p' verify/5/21/2026-05-21-pipeline-bugfix-bundle-targeted-smoke-scope-map.md`
  - 결과: Group A READY, Group B 33개 operator 결정 필요 상태를 확인했습니다.
- `sed -n '1,220p' verify/5/21/2026-05-21-test-web-app-ollama-live-skip-guard.md`
  - 결과: `test_web_app` Ollama live skip guard 이후 `test_smoke + test_web_app` 503개 PASS, skipped=5 상태를 확인했습니다.
- `sed -n '1,220p' work/5/21/2026-05-21-test-web-app-ollama-live-skip-guard.md`
  - 결과: 최신 `/work` closeout을 확인했습니다.
- `git -c core.quotePath=false diff --name-only`
  - 결과: tracked dirty 파일 목록을 확인했습니다.

### 클러스터 1: 문서

- `git diff --check -- .gitignore .pipeline/README.md README.md docs/ACCEPTANCE_CRITERIA.md docs/ARCHITECTURE.md docs/MILESTONES.md docs/PRODUCT_SPEC.md docs/TASK_BACKLOG.md "docs/projectH_pipeline_runtime_docs/03_기술설계_명세서.md" "docs/projectH_pipeline_runtime_docs/05_운영_RUNBOOK.md"`
- 결과: PASS. 출력 없음.

### 클러스터 2: watcher/verify

- `python3 -m py_compile watcher_core.py watcher_dispatch.py watcher_prompt_assembly.py verify_fsm.py`
  - 결과: PASS. 출력 없음.
- `bash -o pipefail -lc 'python3 -m unittest tests.test_watcher_core -v 2>&1 | tail -5'`
  - 결과: `Ran 255 tests in 10.221s` / `OK`.
- `git diff --check -- watcher_core.py watcher_dispatch.py watcher_prompt_assembly.py verify_fsm.py`
  - 결과: PASS. 출력 없음.

### 클러스터 3: web app / controller / launcher

- `python3 -m py_compile app/handlers/reviewed_memory.py app/serializers.py controller/server.py pipeline-launcher.py pipeline_runtime/operator_autonomy.py`
  - 결과: PASS. 출력 없음.
- `bash -o pipefail -lc 'python3 -m unittest tests.test_controller_server tests.test_http_integration -v 2>&1 | tail -5'`
  - 결과: `Ran 84 tests in 12.706s` / `OK`.
- `git diff --check -- app/handlers/reviewed_memory.py app/serializers.py app/static/app.js controller/index.html controller/js/cozy.js controller/js/sidebar.js controller/js/state.js controller/server.py pipeline-launcher.py pipeline_runtime/operator_autonomy.py`
  - 결과: PASS. 출력 없음.
  - 참고: 사용자 명령의 Python 파일 diff check에 더해, 같은 클러스터의 JS/HTML 파일도 whitespace 확인 대상에 포함했습니다.

### 클러스터 4: 테스트 파일 + e2e

- `python3 -m py_compile tests/test_controller_server.py tests/test_http_integration.py tests/test_pipeline_launcher.py tests/test_pipeline_runtime_control_writers.py tests/test_smoke.py tests/test_watcher_core.py tests/test_web_app.py`
  - 결과: PASS. 출력 없음.
- `bash -o pipefail -lc 'python3 -m unittest tests.test_pipeline_runtime_control_writers tests.test_pipeline_launcher -v 2>&1 | tail -5'`
  - 결과: `Ran 45 tests in 0.079s` / `OK`.
- `git diff --check -- tests/test_controller_server.py tests/test_http_integration.py tests/test_pipeline_launcher.py tests/test_pipeline_runtime_control_writers.py tests/test_smoke.py tests/test_watcher_core.py tests/test_web_app.py e2e/tests/controller-smoke.spec.mjs e2e/tests/web-smoke.spec.mjs`
  - 결과: PASS. 출력 없음.
- e2e 실행:
  - 요청 범위상 Playwright/live server가 필요하므로 실행하지 않았습니다.

## 클러스터 판정표

| 클러스터 | 파일 수 | 판정 | 커밋 제목 (제안) |
|---|---:|---|---|
| 1. 문서 | 10 | 커밋 준비 완료 | `docs: sync docs and README` |
| 2. 워처 | 4 | 커밋 준비 완료 | `feat(watcher): harden dispatch and verify recovery` |
| 3. 앱 | 10 | 커밋 준비 완료 | `feat(app): sync controller and launcher surfaces` |
| 4. 테스트 | 9 | 판정 불가 | `test: update runtime and web smoke coverage` |

## operator 커밋 로드맵

1. Group A 별도 커밋을 먼저 진행합니다.
   - 직전 verify 기준 대상: `pipeline_runtime/automation_health.py`, `pipeline_runtime/cli.py`, `pipeline_runtime/supervisor.py`, `tests/test_pipeline_runtime_automation_health.py`, `tests/test_pipeline_runtime_cli.py`, `tests/test_pipeline_runtime_supervisor.py`, `tests/test_web_app.py`.
   - `tests/test_web_app.py`는 Ollama live skip guard 때문에 Group A에 포함하는 것이 자연스럽다는 직전 verify 판정이 있습니다.
2. Group B 클러스터 1 문서 커밋을 진행할 수 있습니다.
   - whitespace check 통과, 테스트 없음.
3. Group B 클러스터 2 watcher/verify 커밋을 진행할 수 있습니다.
   - compile + `tests.test_watcher_core` 255개 + diff check 통과.
4. Group B 클러스터 3 app/controller/launcher 커밋을 진행할 수 있습니다.
   - compile + controller/http unittest 84개 + 전체 클러스터 diff check 통과.
5. Group B 클러스터 4는 Python test subset 기준으로는 양호하지만, e2e 변경 파일이 포함되어 있으므로 operator가 Playwright/live server 검증 실행 여부를 결정한 뒤 커밋하는 것이 안전합니다.

## 남은 리스크

- 클러스터 4의 e2e 파일 2개는 실제 Playwright/live server 검증을 실행하지 않았으므로 `커밋 준비 완료`로 선언하지 않았습니다.
- Group B 파일 내용 자체의 설계 리뷰나 diff 내용 검토는 이번 범위 밖이었습니다.
- untracked 파일은 `git diff --name-only`에 포함되지 않으므로 이번 Group B 33개 분류/판정 대상이 아닙니다.
- commit, push, PR, merge, publish, Playwright, live runtime은 수행하지 않았습니다.
