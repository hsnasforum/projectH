# 2026-05-21 Test web app Ollama live skip guard

## 변경 파일

- `tests/test_web_app.py`
- `work/5/21/2026-05-21-test-web-app-ollama-live-skip-guard.md`

## 사용 skill

- `work-log-closeout`: 변경 파일, 실제 검증 명령, skip 처리 범위, 남은 리스크를 한국어 `/work` 기록으로 남기기 위해 사용했습니다.

## 변경 이유

- `tests.test_web_app` 전체 실행이 live Ollama provider 경로에서 streaming response 대기로 정체될 수 있었습니다.
- CI/로컬 기본 환경에서는 Ollama 모델이 로드되어 있다는 보장이 없으므로, live provider 의존 테스트는 명시적으로 `OLLAMA_LIVE_TESTS=1`일 때만 실행되도록 분리할 필요가 있었습니다.

## 핵심 변경

- `tests/test_web_app.py`에 `import os`를 추가했습니다.
- 처음 지정된 `test_handle_chat_external_fact_colloquial_info_questions_use_web_search_when_enabled`에 `@unittest.skipUnless(os.environ.get("OLLAMA_LIVE_TESTS") == "1", ...)`를 추가했습니다.
- 전체 `test_web_app` 재실행 중 다른 live Ollama provider 경로가 다시 runner를 띄우는 것을 확인해, 같은 범주의 live 의존 테스트 4개에도 동일 guard를 추가했습니다.
  - `test_handle_chat_external_fact_info_uses_web_search_when_enabled`
  - `test_handle_chat_external_fact_who_question_uses_web_search_when_enabled`
  - `test_handle_chat_external_fact_who_question_with_spaced_question_mark_uses_web_search_when_enabled`
  - `test_handle_chat_low_confidence_external_fact_question_returns_search_suggestion`
- adapter를 mock으로 patch하는 Ollama preflight 테스트와 error-localization 테스트는 live 모델 의존이 아니므로 건드리지 않았습니다.

## 검증

- 사전 확인:
  - `sed -n '1,220p' verify/5/21/2026-05-21-pipeline-bugfix-bundle-targeted-smoke-scope-map.md`
  - 결과: 직전 verify에서 `ollama serve`는 있었지만 `ollama runner`가 없고, 문제 테스트가 live Ollama provider를 강제한다는 판정을 확인했습니다.
- 코드 확인:
  - `sed -n '8918,8995p' tests/test_web_app.py`
  - `rg -n '"provider": "ollama"|model_provider="ollama"|ollama_model=' tests/test_web_app.py`
  - 결과: live provider 직접 호출 테스트 5개와 mock-patched Ollama 테스트를 구분했습니다.
- 컴파일:
  - `python3 -m py_compile tests/test_web_app.py`
  - 통과했습니다.
- `test_web_app` 전체 확인:
  - `python3 -m unittest tests.test_web_app -v 2>&1 | grep -E "skip|SKIP|Ran|OK|FAIL|ERROR" | tail -10`
  - 결과: `Ran 334 tests in 10.522s` / `OK (skipped=5)`.
  - 출력에서 live Ollama provider 의존 테스트 5개가 skip으로 표시되었습니다.
- smoke + web_app 결합 확인:
  - `python3 -m unittest tests.test_smoke tests.test_web_app -v 2>&1 | tail -5`
  - 결과: `Ran 503 tests in 11.956s` / `OK (skipped=5)`.
- whitespace 확인:
  - `git diff --check -- tests/test_web_app.py`
  - 통과했습니다.

## 남은 리스크

- `OLLAMA_LIVE_TESTS=1`을 켠 상태에서 실제 `qwen2.5:3b` 모델이 로드된 live Ollama 경로는 이번 라운드에서 실행하지 않았습니다.
- 이번 변경은 `tests/test_web_app.py`의 확인된 live Ollama provider 의존 테스트에만 적용했습니다. 다른 파일의 live Ollama 의존 테스트는 범위 밖이라 탐색하지 않았습니다.
- commit, push, PR, merge, publish, Playwright, E2E, live runtime은 수행하지 않았습니다.
