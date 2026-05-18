# 2026-05-18 publish held local full-smoke guard

## 변경 파일

- `work/5/18/2026-05-18-publish-held-local-full-smoke-guard.md`

## 사용 skill

- `work-log-closeout`: publication held 상태에서 local full-smoke guard 결과, 실행 검증, 남은 리스크를 표준 `/work` 형식으로 기록하는 데 사용했습니다.

## 변경 이유

- `CONTROL_SEQ: 1923` handoff는 publication backlog를 계속 held 상태로 두고, 현재 dirty tree에 대해 `make e2e-test` 기반 local full-smoke guard를 1회 실행하라고 지시했습니다.
- 직전 non-publish local check들은 compile, focused unittest, `doctor --json`, `status --json` 중심이었으므로, 이번 라운드는 로컬 브라우저/socket smoke가 실제로 실행 가능한지와 그 결과를 별도 기록해야 했습니다.

## 핵심 변경

- production code, tests, root instruction docs, prompts, agent rules, product docs는 수정하지 않았습니다.
- commit, push, branch/PR publication, PR creation/reuse, merge, release, external publication, release-ready claim, publication-ready claim, full-smoke-pass readiness claim은 수행하지 않았습니다.
- `make e2e-test`를 1회 실행했습니다. 로컬 서버는 `http://127.0.0.1:8879`에서 기동되었고 Playwright는 `Running 184 tests using 2 workers`까지 진행했습니다.
- 결과는 `6 failed`, `178 passed`, `make: *** [Makefile:13: e2e-test] Error 1`로 실패했습니다.
- 로컬 서버와 Playwright 테스트가 실제로 실행되었으므로 이번 결과는 `local_socket_guard_auto_held`가 아닙니다. socket permission denial 또는 local server startup denial로 held 처리하지 않았습니다.
- 실패가 controller/browser/preference UI smoke 영역에 걸쳐 있고 이번 handoff의 `PRIMARY_WRITE_SCOPE` 안에서 안전하게 고칠 수 있는 직접적인 작은 runtime/source/test 결함으로 한정되지 않아, 코드/테스트 수정 없이 결과를 기록하고 멈췄습니다.

## 검증

- `make e2e-test`
  - 실패했습니다. `6 failed`, `178 passed (17.5m)`, exit code 2.
  - `tests/controller-smoke.spec.mjs:530:3` `controller office smoke › controller shows active verify owner as working even when lane snapshot is ready`
    - `page.waitForFunction(() => window.getAgentPositions?.()?.Claude?.state === "working")`가 60초 timeout으로 실패했습니다.
  - `tests/web-smoke.spec.mjs:224:1` `브라우저 폴더 선택으로도 문서 검색이 됩니다`
    - 예상 문자열 `[모의 요약]` 대신 `[모의 요약, 선호 2건 반영] ...` 응답이 표시되었습니다.
  - `tests/web-smoke.spec.mjs:278:1` `검색만 응답은 transcript에서 preview cards만 보이고 본문 텍스트는 숨겨집니다`
    - 예상 문자열 `[모의 요약]` 대신 `[모의 요약, 선호 2건 반영] ...` 응답이 표시되었습니다.
  - `tests/web-smoke.spec.mjs:420:1` `내용 거절은 approval을 유지하고 나중 explicit save로 supersede 됩니다`
    - approval preview 예상 문자열 `[모의 요약]` 대신 `[모의 요약, 선호 2건 반영] ...` 응답이 표시되었습니다.
  - `tests/web-smoke.spec.mjs:14009:1` `preference auto activation notice appears in PreferencePanel after correction`
    - `getByTitle('수정')`가 disabled `수정본 저장` 버튼과 실제 `수정` 버튼 2개를 함께 찾아 strict mode violation으로 실패했습니다.
  - `tests/web-smoke.spec.mjs:14273:1` `reviewed-memory loop: 활성화된 선호가 PreferencePanel 이번 응답 반영 배지에 표시됩니다`
    - `getByRole('button', { name: '활성화' })`가 넓은 이름의 카드 버튼과 작은 `활성화` 버튼 2개를 함께 찾아 strict mode violation으로 실패했습니다.
- `git diff --check -- verify_fsm.py watcher_core.py watcher_dispatch.py watcher_prompt_assembly.py tests/test_pipeline_runtime_supervisor.py tests/test_verify_fsm.py tests/test_watcher_core.py work/5/18/2026-05-18-publish-held-local-full-smoke-guard.md`
  - closeout 작성 후 기준 출력 없이 통과했습니다.
- `git status --short -- verify_fsm.py watcher_core.py watcher_dispatch.py watcher_prompt_assembly.py tests/test_pipeline_runtime_supervisor.py tests/test_verify_fsm.py tests/test_watcher_core.py work/5/18/2026-05-18-publish-held-local-full-smoke-guard.md .pipeline/implement_handoff.md .pipeline/operator_request.md .pipeline/advisory_request.md`
  - 아래 scoped dirty state를 확인했습니다.
  - `M tests/test_pipeline_runtime_supervisor.py`
  - `M tests/test_verify_fsm.py`
  - `M tests/test_watcher_core.py`
  - `M verify_fsm.py`
  - `M watcher_core.py`
  - `M watcher_dispatch.py`
  - `M watcher_prompt_assembly.py`
  - `?? work/5/18/2026-05-18-publish-held-local-full-smoke-guard.md`

## 남은 리스크

- local full-smoke guard는 실패했습니다. 이번 라운드에서 release-ready, publication-ready, full-smoke-pass readiness를 주장하지 않습니다.
- 실패 6건은 controller smoke, document/web smoke, reviewed-memory/preference UI smoke 영역에 남아 있습니다.
- 이번 handoff 범위상 controller/browser product smoke 결함 수정, broad E2E triage, root docs churn, next-slice 선택은 수행하지 않았습니다.
- dirty tree는 그대로 보존했습니다. stash apply/pop/drop/clear/branch/store/rewrite/discard는 수행하지 않았습니다.
