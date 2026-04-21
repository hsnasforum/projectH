# 2026-04-21 stale control advisory routing

## 변경 파일
- `watcher_core.py`
- `pipeline_runtime/automation_health.py`
- `tests/test_watcher_core.py`
- `tests/test_pipeline_runtime_automation_health.py`
- `work/4/21/2026-04-21-stale-control-advisory-routing.md`

## 사용 skill
- `security-gate`: stale control 감지가 `.pipeline/gemini_request.md` 쓰기만 수행하고, 기존 `claude_handoff.md`/`operator_request.md`를 수정하지 않으며 실패 시 poll을 죽이지 않는지 확인했습니다.
- `finalize-lite`: 실행한 검증, 문서 동기화 범위, `/work` closeout 필요성을 구현 종료 전에 정리했습니다.
- `work-log-closeout`: 실제 변경 파일과 실행한 명령만 기준으로 이 closeout을 남겼습니다.

## 변경 이유
- 이전 round는 `stale_control_seq=true`를 status에 노출했지만, 장시간 같은 `CONTROL_SEQ`가 유지될 때 후속 라우팅은 없었습니다.
- 이번 handoff는 stale 감지 후 추가 grace 기간이 지나면 operator stop이 아니라 advisory-first로 triage가 열리도록 요구했습니다.

## 핵심 변경
- `pipeline_runtime/automation_health.py`에 `STALE_ADVISORY_GRACE_CYCLES=60`을 추가하고, health payload에 `stale_advisory_grace_cycles`와 `stale_advisory_pending`을 노출했습니다.
- watcher가 `STALE_CONTROL_CYCLE_THRESHOLD + STALE_ADVISORY_GRACE_CYCLES`에 도달하면 `REASON_CODE: stale_control_advisory`를 담은 `.pipeline/gemini_request.md`를 atomically 작성하도록 했습니다.
- 기존 `.pipeline/gemini_request.md`가 같은 reason code이고 `CONTROL_SEQ`가 현재 추적 seq 이상이면 덮어쓰지 않는 idempotency guard를 추가했습니다.
- `.pipeline/claude_handoff.md`와 `.pipeline/operator_request.md`는 읽기만 하며, advisory request write 실패 및 실패 로그 기록 실패도 warning 후 계속 진행하도록 fail-closed 처리했습니다.
- 새 advisory request 작성 시 runtime raw/event 로그를 남기고 watcher turn을 `ADVISORY_ACTIVE`로 전환해 advisory lane 알림까지 이어지게 했습니다.

## 검증
- `python3 -m py_compile watcher_core.py pipeline_runtime/automation_health.py` → 통과
- `python3 -m unittest tests.test_pipeline_runtime_automation_health tests.test_watcher_core.ControlSeqAgeTrackerTest` → 22 tests OK
- `python3 -m unittest tests.test_pipeline_runtime_automation_health tests.test_watcher_core` → 190 tests OK
- `git diff --check watcher_core.py pipeline_runtime/automation_health.py tests/test_watcher_core.py tests/test_pipeline_runtime_automation_health.py` → 통과
- `sha256sum .pipeline/claude_handoff.md` → `5a8c108278746cebaecc4548c377f51db1c4ee1d1cb17e44af9a4045c348915c` 유지 확인

## 남은 리스크
- 이번 round는 handoff 지정 범위에 맞춰 watcher/core health와 단위 테스트만 바꿨습니다. launcher/GUI/docs surface에는 새 `stale_advisory_pending` 표시를 추가하지 않았습니다.
- 실제 운영에서 stale control이 operator stop인 경우에도 advisory request가 더 높은 `CONTROL_SEQ`로 열릴 수 있습니다. 이는 이번 handoff의 advisory-first 요구에 맞춘 동작이며, verify/handoff owner가 이후 정책 적합성을 확인해야 합니다.
- worktree에는 이전 seq 691/697 계열 dirty 변경이 함께 남아 있습니다. 이번 round는 해당 변경을 되돌리거나 commit/push하지 않았습니다.
