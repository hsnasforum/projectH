# 2026-05-21 Stale handoff dispatch fail-closed

## 변경 파일

- `pipeline_runtime/supervisor.py`
- `tests/test_pipeline_runtime_supervisor.py`
- `work/5/21/2026-05-21-stale-handoff-dispatch-fail-closed.md`

## 사용 skill

- `security-gate`: runtime dispatch 차단, 이벤트 payload, 재주입 방지 경계를 점검하기 위해 사용했습니다.
- `work-log-closeout`: 변경 파일, 실제 검증, 남은 리스크를 한국어 `/work` 기록으로 남기기 위해 사용했습니다.

## 변경 이유

- 재시작 후 오래된 `STATUS: implement` handoff가 artifact truth나 명시적 `REISSUE: true` 없이 Codex pane에 자동 재주입되는 사고를 막기 위함입니다.
- 완료를 work-only로 추정하지 않고, 검증되지 않은 오래된 지시는 fail-closed로 차단하는 방향을 적용했습니다.

## 핵심 변경

- `_duplicate_control_marker()`에 `REISSUE: true` 단순 regex 체크를 추가했습니다.
- `completed_implement_handoff_truth()`가 `None`이고, runtime dispatch가 가능한 supervisor에서 `active_control_updated_at < self.started_at`인 오래된 handoff를 `stale_handoff_dispatch_blocked`로 차단합니다.
- 차단 marker에는 `control_file`, `control_seq`, `handoff_sha`, `routed_to`, `source_event`, `stale_age_sec`만 담고 raw pane text나 control 본문은 담지 않습니다.
- `_record_status_events()`가 stale marker를 `stale_handoff_dispatch_blocked` event로 기록합니다.
- `start_runtime=False`인 상태 조회/테스트용 supervisor에는 stale dispatch gate를 적용하지 않도록 해, dispatch하지 않는 read-only surface가 control state를 임의로 지우지 않게 했습니다.
- 기존 raw-log duplicate 테스트에는 `REISSUE: true`를 명시해 stale 차단 우회 후 raw truth 경로가 계속 검증되도록 조정했습니다.

## 검증

- `python3 -m py_compile pipeline_runtime/supervisor.py`
  - 통과했습니다.
- `python3 -m unittest tests.test_pipeline_runtime_supervisor -v`
  - 통과했습니다. `Ran 207 tests`
- `git diff --check -- pipeline_runtime/supervisor.py tests/test_pipeline_runtime_supervisor.py`
  - 통과했습니다.

## 남은 리스크

- 신규 automation incident family나 controller 표시 변경은 이번 범위에서 추가하지 않았습니다. 현재는 `control_duplicate_ignored`와 `stale_handoff_dispatch_blocked` event로 관측합니다.
- `REISSUE: true` 작성 UI나 operator flow는 없습니다. 의도적 재실행은 handoff 본문에 명시적으로 마커를 넣는 방식입니다.
- `.pipeline/README.md` 같은 runtime 운영 문서 업데이트는 이번 handoff 범위 밖이라 수행하지 않았습니다.
- commit, push, PR, merge, publish는 수행하지 않았습니다.
