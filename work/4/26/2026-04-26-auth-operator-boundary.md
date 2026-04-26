# 2026-04-26 auth operator boundary

## 변경 파일
- `.pipeline/README.md`
- `README.md`
- `pipeline_runtime/operator_autonomy.py`
- `tests/test_operator_request_schema.py`
- `tests/test_pipeline_runtime_supervisor.py`
- `work/4/26/2026-04-26-auth-operator-boundary.md`
- `work/4/26/2026-04-26-m42-watcher-core-reexport-normalization.md`

## 사용 skill
- `security-gate`: auth/credential stop이 false-stop demotion에 섞여 operator 경계를 우회하지 않는지 확인했다.
- `doc-sync`: README와 `.pipeline/README.md`의 runtime/operator boundary 설명을 현재 구현 truth에 맞췄다.
- `finalize-lite`: 구현 종료 전 검증, 문서 동기화, `/work` closeout 준비 상태를 좁게 확인했다.
- `work-log-closeout`: 변경 파일, 서브에이전트 감사 결과, 검증, 잔여 리스크를 기록했다.

## 변경 이유
- `approval-auditor` 서브에이전트가 `auth_login_required`의 구현/문서 불일치를 지적했다. 문서와 operator contract는 auth/credential을 실제 operator-visible 경계로 보지만, shared evaluator에서는 `_GATED_REASON_CODES`에 있어 `gate_24h` 조합에서 verify follow-up으로 낮아질 수 있었다.
- false-stop reduction은 agent가 좁힐 수 있는 release-gate follow-up을 줄이는 목적이지, 인증/credential 복구를 자동화하는 범위가 아니다.
- `planner` 서브에이전트는 watcher/supervisor operator-stop resolution 추출을 다음 큰 정리 후보로 제안했지만, 이번 라운드에서는 이미 진행 중인 dirty watcher slice와 섞지 않고 auth safety boundary만 작은 보정으로 닫았다.

## 핵심 변경
- `pipeline_runtime/operator_autonomy.py`에서 `auth_login_required`를 `_GATED_REASON_CODES`에서 `_IMMEDIATE_REASON_CODES`로 옮겨 `gate_24h`가 붙어도 `needs_operator` / `routed_to=operator`로 남게 했다.
- `tests/test_operator_request_schema.py`에 `test_auth_login_required_stays_operator_visible`을 추가해 supported reason, `needs_operator`, `operator_eligible=True`, gate marker 없음까지 고정했다.
- `tests/test_pipeline_runtime_supervisor.py`에 `test_classify_operator_candidate_auth_login_stays_operator_visible`을 추가해 supervisor가 shared evaluator 결과를 operator-visible로 보존하는지 확인했다.
- README runtime section과 `.pipeline/README.md`에 `auth_login_required` / credential/auth repair 계열은 false-stop demotion 대상이 아니라 즉시 operator-visible 경계라고 명시했다.
- 병행 dirty slice인 `watcher_core.py` re-export 정리는 코드를 새로 고치지 않고 기존 변경을 검증했으며, 관련 closeout에 pipeline 자동화/호환성 관점과 검증 결과를 보강했다.

## 검증
- `python3 -m unittest -v tests.test_operator_request_schema` 통과
  - `Ran 30 tests in 0.006s`
- `python3 -m unittest -v tests.test_watcher_core` 통과
  - `Ran 204 tests in 9.043s`
- `python3 -m unittest -v tests.test_pipeline_runtime_supervisor tests.test_pipeline_runtime_automation_health` 통과
  - `Ran 171 tests in 1.189s`
- `python3 -m py_compile pipeline_runtime/operator_autonomy.py pipeline_runtime/supervisor.py watcher_core.py watcher_prompt_assembly.py` 통과, 출력 없음
- `git diff --check -- pipeline_runtime/operator_autonomy.py pipeline_runtime/supervisor.py watcher_core.py watcher_prompt_assembly.py README.md .pipeline/README.md tests/test_operator_request_schema.py tests/test_pipeline_runtime_supervisor.py tests/test_watcher_core.py work/4/26/2026-04-26-m42-watcher-core-reexport-normalization.md` 통과, 출력 없음
- `rg -n "[ \t]+$" work/4/26/2026-04-26-auth-operator-boundary.md` 통과, trailing whitespace 없음

## 남은 리스크
- live supervisor/watcher soak, controller browser smoke, PR publish flow는 실행하지 않았다. 이번 변경은 shared evaluator 분류와 관련 단위 회귀에 한정했다.
- subagent planner가 제안한 watcher/supervisor shared operator control resolver 추출은 다음 coherent slice 후보로 남겼다. 이번 라운드에서 같이 구현하면 기존 dirty watcher_core re-export 변경과 섞여 리뷰 범위가 커질 수 있어 제외했다.
- 기존 dirty tree의 `watcher_core.py`, `tests/test_watcher_core.py`, `verify/4/25/2026-04-25-m36-preference-pause-functional-e2e.md`, `report/gemini/**`, 선행 `/work` 미추적 파일들은 이번 라운드에서 되돌리거나 정리하지 않았다.
- commit, push, branch/PR 생성, merge는 수행하지 않았다.
