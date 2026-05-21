# 2026-05-21 publish-held compat queue snapshot guard

## 변경 파일

- `pipeline_runtime/state_contract.py`
- `tests/test_pipeline_runtime_state_contract.py`
- `work/5/21/2026-05-21-publish-held-compat-queue-snapshot-guard.md`

## 사용 skill

- `security-gate`: runtime/control surface가 operator stop이나 publication 승인처럼 보이지 않도록 local-only 경계와 commit/push/PR/merge/release 금지를 점검했다.
- `work-log-closeout`: 변경 파일, 실제 검증, 남은 리스크를 한국어 `/work` 기록으로 남기기 위해 사용했다.

## 변경 이유

- `.pipeline/operator_request.md#2072`는 shared resolver 기준 local-only held publication metadata이고 canonical status에서는 `control=none`, `automation_health=ok`, `automation_next_action=continue`로 내려간 상태였다.
- 그런데 `runtime_snapshot.queue`가 compat active slot만 보고 `needs_operator #2072`를 active queued task처럼 표시하고 `active_control_slot_not_surfaced` invariant를 남길 수 있었다.
- thin client가 compat slot을 current truth로 재승격하지 않도록, canonical status가 이미 계속 진행 상태로 낮춘 compat `operator_request.md`만 snapshot queue에서 debug-only로 취급해야 했다.

## 핵심 변경

- `pipeline_runtime/state_contract.py`에 `_compat_operator_candidate_is_suppressed()`를 추가해 `control=none`, `automation_health=ok`, `automation_next_action=continue`, reason 없음, compat `operator_request.md + needs_operator` 조합만 suppressed candidate로 판정한다.
- `_queue_snapshot()`은 suppressed compat operator candidate를 queued control로 세지 않고, active round가 있으면 round 상태를 우선 표시하며 active round가 없으면 empty queue로 둔다.
- `no_queue_with_active_control_slot`와 `active_control_slot_not_surfaced` invariant는 suppressed compat operator candidate에는 붙이지 않고, genuine compat mismatch에는 계속 남긴다.
- `suppressed_operator_candidate` snapshot flag도 compat suppressed operator candidate를 반영하게 했다.
- `tests/test_pipeline_runtime_state_contract.py`에 suppressed compat operator queue, active round 우선 표시, non-continuing operator compat mismatch 회귀를 추가했다.

## 검증

- `python3 -m py_compile pipeline_runtime/state_contract.py tests/test_pipeline_runtime_state_contract.py`
  - 통과.
- `python3 -m unittest -v tests.test_pipeline_runtime_state_contract`
  - 통과. `Ran 8 tests in 0.001s`, `OK`.
- `git diff --check -- pipeline_runtime/state_contract.py tests/test_pipeline_runtime_state_contract.py tests/test_pipeline_runtime_supervisor.py README.md .pipeline/README.md docs/projectH_pipeline_runtime_docs/03_기술설계_명세서.md docs/projectH_pipeline_runtime_docs/05_운영_RUNBOOK.md`
  - 통과. 출력 없음.
- synthetic `reduce_runtime_snapshot(...)` 확인
  - compat `operator_request.md#2072`, canonical `control=none`, `automation_health=ok`, `automation_next_action=continue`, active round `VERIFYING` 입력에서 `queue_status=VERIFYING`, `suppressed_operator_candidate=True`, `violations=`로 확인했다.
- `rg -n "[ \t]+$" pipeline_runtime/state_contract.py tests/test_pipeline_runtime_state_contract.py`
  - trailing whitespace match 없음.

## 남은 리스크

- `tests/test_pipeline_runtime_supervisor.py`는 변경하지 않았고 별도 supervisor regression은 실행하지 않았다. 이번 수정은 reducer-only contract로 제한했다.
- controller/Playwright/full e2e/long soak는 실행하지 않았다. controller는 `runtime_snapshot.queue`를 우선 읽는 기존 계약을 따르므로 이번 라운드에서는 state contract unit으로 검증 범위를 제한했다.
- 작업트리는 이전 라운드의 여러 dirty 파일과 untracked work/verify 기록을 계속 포함한다. 이번 closeout은 `state_contract` queue snapshot guard 변경만 귀속한다.
- commit, push, branch/PR publication, PR creation, merge, release는 실행하지 않았고 계속 held 상태다.
