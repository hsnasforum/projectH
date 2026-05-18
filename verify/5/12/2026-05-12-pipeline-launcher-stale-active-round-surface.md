STATUS: verified

# 2026-05-12 Pipeline launcher stale active_round surface 검증

## 대상

- `work/5/12/2026-05-12-pipeline-launcher-stale-active-round-surface.md`

## 변경 파일

- 없음

## 결론

- 통과입니다. 최신 `/work`의 stale `active_round` suppression, `READY/closed` implement idle 표면화, Codex stale pasted prompt 교체 및 Enter 재시도 변경은 단위 회귀, compile, whitespace check 기준으로 현재 코드와 일치합니다.
- 구현 범위는 원래 `CONTROL_SEQ 1621` handoff의 allowed files보다 넓어졌지만, 최신 `/work`가 명시한 변경 파일과 검증 범위 기준으로는 관련 런처 runtime/supervisor/watcher 경로에 한정되어 있습니다.
- 이 노트를 쓰기 전 live status는 최신 work에 대한 현재 verify 라운드가 진행 중인 상태로 보였고, `artifacts.latest_verify.path`는 아직 `—`였습니다. 이 파일을 matching verify receipt로 남긴 뒤 status 수렴을 다시 확인해야 합니다.

## 확인한 사실

- `pipeline_runtime/supervisor.py`는 `duplicate_control`이 확인된 뒤 `control_block`을 `none`으로 표면화하고, 최신 work/verify가 matching이며 idle duplicate handoff 상태일 때 오래된 verify `active_round`를 suppress하는 helper를 포함합니다.
- `pipeline_runtime/automation_health.py`는 `READY/closed` active implement lane을 `implement_active_idle` attention으로 다루고, non-degraded `VERIFY_PENDING` dispatch wait는 `recovering/retrying`, degraded `dispatch_stall`은 `attention/verify_followup`으로 구분합니다.
- `watcher_dispatch.py`는 idle prompt에 `[Pasted Content ...]`가 남은 경우 일반 idle로 보지 않고 stale pasted prompt replacement 경로로 보내며, Codex dispatch 직전 `C-c` + `C-u` 정리와 붙여넣기 후 Enter 1회 재시도를 수행합니다.
- `.pipeline/README.md`는 no-silent-stall 계약에 duplicate handoff / waiting_next_control family, stale active round suppression, role-neutral advisory log wording, current profile lane 예시를 반영했습니다.
- live status 조회 결과 이 노트 작성 전에는:
  - `runtime_state=RUNNING`
  - `control.active_control_status=implement`
  - `control.active_control_seq=1621`
  - `active_round.artifact_path=.../work/5/12/2026-05-12-pipeline-launcher-stale-active-round-surface.md`
  - `active_round.state=VERIFYING`
  - `turn_state.state=VERIFY_ACTIVE`
  - `artifacts.latest_work.path=5/12/2026-05-12-pipeline-launcher-stale-active-round-surface.md`
  - `artifacts.latest_verify.path=—`
- 이 노트 작성 뒤 live status는 matching verify를 반영해 다음 상태로 수렴했습니다:
  - `control.active_control_status=none`
  - `turn_state.state=IDLE`
  - `turn_state.reason=handoff_already_completed`
  - Codex lane `READY`, note `waiting_next_control`
  - `artifacts.latest_work.path=5/12/2026-05-12-pipeline-launcher-stale-active-round-surface.md`
  - `artifacts.latest_verify.path=5/12/2026-05-12-pipeline-launcher-stale-active-round-surface.md`
  - `automation_health=attention`
  - `automation_reason_code=duplicate_handoff`
  - `automation_next_action=verify_followup`
- 노트 작성 뒤 `active_round`는 예전 work가 아니라 이번 verify job의 `receipt_close_pending` 상태입니다. 즉 이번 검증 대상이던 "오래된 work의 stale active_round" 재현은 아니며, anti-stall 계약상 더 높은 `CONTROL_SEQ`의 다음 control이 필요합니다.

## 실행한 검증

- PASS: `python3 -m unittest -v tests.test_pipeline_runtime_automation_health tests.test_pipeline_runtime_supervisor.RuntimeSupervisorTest tests.test_watcher_core`
  - 412 tests
- PASS: `python3 -m py_compile pipeline_runtime/automation_health.py pipeline_runtime/supervisor.py watcher_dispatch.py tests/test_pipeline_runtime_automation_health.py tests/test_pipeline_runtime_supervisor.py tests/test_watcher_core.py`
- PASS: `git diff --check -- .pipeline/README.md pipeline_runtime/automation_health.py pipeline_runtime/supervisor.py watcher_dispatch.py tests/test_pipeline_runtime_automation_health.py tests/test_pipeline_runtime_supervisor.py tests/test_watcher_core.py work/5/12/2026-05-12-pipeline-launcher-stale-active-round-surface.md verify/5/12/2026-05-12-pipeline-launcher-nonstop-guard.md`
- PASS: `python3 -m pipeline_runtime.cli status --json /home/xpdlqj/code/projectH`
  - 노트 작성 전 1회, 노트 작성 뒤 1회

## 실행하지 않은 검증

- browser/E2E는 실행하지 않았습니다. 이번 변경은 런처 runtime status, supervisor active-round 선택, automation health 파생, watcher dispatch 단위 경로에 한정됩니다.
- live restart는 이번 검증 턴에서 재실행하지 않았습니다. 현재 live `run_id=20260512T061355Z-p155898`는 최신 work mtime 이후 시작된 실행으로 보이며, 이번 검증은 현재 status 조회와 단위 회귀로 제한했습니다.
- 장시간 soak는 실행하지 않았습니다.

## 남은 리스크

- worktree에는 이번 범위 밖의 파이프라인/문서/GUI 변경과 여러 untracked `work/`, `verify/`, `report/gemini/` 기록이 남아 있습니다.
- commit/push/PR publish는 implement lane에 넘길 수 없는 운영 경계입니다. 검증 완료 후 다음 제어는 publish 경계와 다음 구현 후보를 섞지 않고 하나만 선택해야 합니다.
