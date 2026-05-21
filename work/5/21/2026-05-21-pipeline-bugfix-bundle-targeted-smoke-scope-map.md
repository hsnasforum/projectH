# 2026-05-21 Pipeline bugfix bundle targeted smoke scope map

## 변경 파일

- `work/5/21/2026-05-21-pipeline-bugfix-bundle-targeted-smoke-scope-map.md`

## 사용 skill

- `work-log-closeout`: 검증 라운드의 실제 명령 결과, web app hang 판정, dirty diff 분류표를 한국어 `/work` 기록으로 남기기 위해 사용했습니다.

## 변경 이유

- 직전 라운드에서 `tests.test_web_app` 전체 실행이 Ollama streaming response 대기에서 정체되어 pipeline_runtime 회귀인지 환경 의존 테스트 문제인지 분리 판정이 필요했습니다.
- tracked dirty 파일 39개가 pipeline_runtime 번들과 다른 라운드 산출물로 섞여 있어, commit/publish 전 operator가 범위를 판단할 수 있게 분류표가 필요했습니다.

## 핵심 변경

- 코드 변경 없음.
- `tests.test_smoke` 전체를 분리 실행해 mock 경로 web/app smoke가 통과하는지 확인했습니다.
- `tests.test_web_app -k "not colloquial"`은 Python `unittest`에서 제외식으로 동작하지 않아 `Ran 0 tests`로 끝나는 것을 확인했습니다.
- STOP_RULES의 fallback에 따라 `tests.test_web_app` 앞부분 실행 로그로 import 단계 오류가 없는지 확인했습니다.
- `tests/test_web_app.py`의 정체 테스트가 payload에서 `"provider": "ollama"`와 `"model": "qwen2.5:3b"`를 강제하는 것을 확인했습니다.
- `git diff --name-only` 기준 tracked dirty 39개 파일을 그룹 A/B로 분류했습니다. untracked 파일은 이 표의 대상이 아닙니다.

## 검증

- 직전 `/work` 확인:
  - `sed -n '1,260p' work/5/21/2026-05-21-pipeline-bugfix-bundle-smoke-verification.md`
  - 결과: 직전 전체 smoke가 `tests.test_web_app.WebAppServiceTest.test_handle_chat_external_fact_colloquial_info_questions_use_web_search_when_enabled`에서 Ollama streaming 대기로 중단된 기록을 확인했습니다.
- smoke 단독 확인:
  - `python3 -m unittest tests.test_smoke -v`
  - 결과: `Ran 169 tests in 1.142s` / `OK`.
- web_app 제외 필터 확인:
  - `python3 -m unittest tests.test_web_app -v -k "not colloquial"`
  - 결과: `Ran 0 tests in 0.000s` / `NO TESTS RAN`, exit code 5.
  - 판정: 이 환경의 `unittest -k`는 `not colloquial`을 제외식으로 해석하지 않아 성공 기준용 필터로 사용할 수 없었습니다.
- fallback import/초반 실행 확인:
  - `timeout 20s bash -lc 'python3 -m unittest tests.test_web_app -v 2>&1 | head -300'`
  - 결과: timeout exit code 124. 출력된 범위에서는 web_app 테스트들이 import 단계에서 실패하지 않고 다수 `ok`로 진행했습니다. 즉시 import 회귀 증거는 없었습니다.
- 정체 테스트 코드 확인:
  - `sed -n '8918,8995p' tests/test_web_app.py`
  - `nl -ba tests/test_web_app.py | sed -n '8948,8988p'`
  - 결과: `test_handle_chat_external_fact_colloquial_info_questions_use_web_search_when_enabled`는 `AppSettings(model_provider="mock")`를 만들지만, 실제 `service.handle_chat()` payload에서 `"provider": "ollama"`와 `"model": "qwen2.5:3b"`를 전달합니다.
- Ollama 프로세스 확인:
  - `ps -o pid,ppid,stat,etime,cmd -u "$USER" | rg "ollama serve|ollama runner" || true`
  - 결과: `ollama serve` 프로세스는 존재했고, 이 시점에 `ollama runner`는 없었습니다.
- 남은 unittest 프로세스 확인:
  - `ps -o pid,ppid,stat,etime,cmd -u "$USER" | rg "python3 -m unittest tests.test_web_app|tests.test_web_app|tests.test_smoke" || true`
  - 결과: 남은 해당 unittest 프로세스 없음.
- dirty 파일 목록 확인:
  - `git diff --name-only`
  - `git -c core.quotePath=false diff --name-only`
  - 결과: tracked dirty 파일 39개 확인.

## 판정

- `tests.test_smoke` 전체가 통과했으므로 mock 기반 smoke 경로에서 pipeline_runtime 변경이 web app import를 깨는 증거는 없습니다.
- `tests.test_web_app -k "not colloquial"`은 실제 테스트를 실행하지 않았기 때문에 "통과"로 인정하지 않았습니다.
- fallback 출력과 직전 스택 기준, 문제의 hang은 `tests/test_web_app.py:8928` 테스트가 `tests/test_web_app.py:8985`에서 `"provider": "ollama"`를 강제해 Ollama live model review path로 들어간 환경 의존 정체입니다. pipeline_runtime 회귀로 볼 증거는 없습니다.
- 단, 이번 라운드는 full `tests.test_web_app` filtered pass를 얻은 것은 아니므로 web_app 전체 PASS를 주장하지 않습니다.
- 그룹 A(pipeline_runtime 번들)는 지금까지의 pipeline_runtime 전용 테스트, `tests.test_smoke` 통과, web_app import fallback 관찰 기준으로 commit 후보로 분리 가능합니다.
- 그룹 B는 별도 라운드 산출물이며, 이번 pipeline_runtime 번들과 함께 commit할지 여부는 operator 결정이 필요합니다.

## dirty worktree 분류

| 그룹 | 파일 | 판정 |
|---|---|---|
| A | `pipeline_runtime/automation_health.py` | pipeline_runtime 번들 |
| A | `pipeline_runtime/cli.py` | pipeline_runtime 번들 |
| A | `pipeline_runtime/supervisor.py` | pipeline_runtime 번들 |
| A | `tests/test_pipeline_runtime_automation_health.py` | pipeline_runtime 번들 테스트 |
| A | `tests/test_pipeline_runtime_cli.py` | pipeline_runtime 번들 테스트 |
| A | `tests/test_pipeline_runtime_supervisor.py` | pipeline_runtime 번들 테스트 |
| B | `.gitignore` | 별도 라운드 산출물 |
| B | `.pipeline/README.md` | 별도 라운드 산출물 |
| B | `README.md` | 별도 라운드 산출물 |
| B | `app/handlers/reviewed_memory.py` | 별도 라운드 산출물 |
| B | `app/serializers.py` | 별도 라운드 산출물 |
| B | `app/static/app.js` | 별도 라운드 산출물 |
| B | `controller/index.html` | 별도 라운드 산출물 |
| B | `controller/js/cozy.js` | 별도 라운드 산출물 |
| B | `controller/js/sidebar.js` | 별도 라운드 산출물 |
| B | `controller/js/state.js` | 별도 라운드 산출물 |
| B | `controller/server.py` | 별도 라운드 산출물 |
| B | `docs/ACCEPTANCE_CRITERIA.md` | 별도 라운드 산출물 |
| B | `docs/ARCHITECTURE.md` | 별도 라운드 산출물 |
| B | `docs/MILESTONES.md` | 별도 라운드 산출물 |
| B | `docs/PRODUCT_SPEC.md` | 별도 라운드 산출물 |
| B | `docs/TASK_BACKLOG.md` | 별도 라운드 산출물 |
| B | `docs/projectH_pipeline_runtime_docs/03_기술설계_명세서.md` | 별도 라운드 산출물 |
| B | `docs/projectH_pipeline_runtime_docs/05_운영_RUNBOOK.md` | 별도 라운드 산출물 |
| B | `e2e/tests/controller-smoke.spec.mjs` | 별도 라운드 산출물 |
| B | `e2e/tests/web-smoke.spec.mjs` | 별도 라운드 산출물 |
| B | `pipeline-launcher.py` | 별도 라운드 산출물 |
| B | `pipeline_runtime/operator_autonomy.py` | 별도 라운드 산출물 |
| B | `tests/test_controller_server.py` | 별도 라운드 산출물 |
| B | `tests/test_http_integration.py` | 별도 라운드 산출물 |
| B | `tests/test_pipeline_launcher.py` | 별도 라운드 산출물 |
| B | `tests/test_pipeline_runtime_control_writers.py` | 별도 라운드 산출물 |
| B | `tests/test_smoke.py` | 별도 라운드 산출물 |
| B | `tests/test_watcher_core.py` | 별도 라운드 산출물 |
| B | `tests/test_web_app.py` | 별도 라운드 산출물 |
| B | `verify_fsm.py` | 별도 라운드 산출물 |
| B | `watcher_core.py` | 별도 라운드 산출물 |
| B | `watcher_dispatch.py` | 별도 라운드 산출물 |
| B | `watcher_prompt_assembly.py` | 별도 라운드 산출물 |

## 남은 리스크

- `tests.test_web_app -k "not colloquial"`은 0 tests라 성공 기준을 문자 그대로 만족하지 못했습니다.
- full `tests.test_web_app`는 여전히 Ollama live provider 경로 때문에 정체될 수 있습니다.
- `ollama serve` 프로세스는 존재했으므로 이번 기록에서는 "Ollama 서버 미실행"으로 단정하지 않았습니다. 확인된 사실은 `"provider": "ollama"` 강제와 streaming response 대기입니다.
- Group A만 commit하려면 staged 파일을 6개로 엄격히 제한해야 합니다. Group B와 untracked 파일은 operator가 별도 포함 여부를 결정해야 합니다.
- commit, push, PR, merge, publish, Playwright, E2E, live runtime은 수행하지 않았습니다.
