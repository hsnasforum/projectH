# 2026-04-22 active control snapshot

## 변경 파일
- `pipeline_runtime/schema.py`
- `watcher_core.py`
- `pipeline_runtime/supervisor.py`
- `tests/test_pipeline_runtime_schema.py`
- `work/4/22/2026-04-22-active-control-snapshot.md`

## 사용 skill
- `security-gate`: runtime control/status JSON 경로를 건드리는 변경이므로 local-first, control slot, audit/status 경계를 확인했습니다.
- `finalize-lite`: 필수 검증 통과 여부와 문서 동기화 필요 여부를 구현 종료 기준으로 점검했습니다.
- `work-log-closeout`: 실제 변경 파일, 실행 명령, 남은 리스크를 기준으로 이 closeout을 작성했습니다.

## 변경 이유
- `.pipeline/implement_handoff.md` CONTROL_SEQ 742의 `shared_state_parsing_snapshot` slice를 구현하기 위해서입니다.
- watcher와 supervisor가 active pipeline control slot을 서로 다른 string-key 조합으로 읽고 쓰던 부분을 `ActiveControlSnapshot` typed shared state로 모아, status/control 파싱 drift를 줄이기 위해서입니다.

## 핵심 변경
- `pipeline_runtime/schema.py`에 `ActiveControlSnapshot` `TypedDict`와 `active_control_snapshot_from_entry()`, `active_control_snapshot_from_status()` helper를 추가했습니다.
- `watcher_core.py`의 runtime status writer와 turn transition 기록이 snapshot helper를 거쳐 기존 `active_control_*` JSON key를 쓰도록 변경했습니다. `status.json`의 key 이름은 유지했습니다.
- `pipeline_runtime/supervisor.py`의 active control path, duplicate handoff marker, stale operator marker, operator gate marker, lane/task hint/status event reader를 snapshot 기반으로 정리했습니다.
- supervisor status producer는 `parse_control_slots()` active entry를 snapshot으로 변환한 뒤 기존 `active_control_*` control block을 만들도록 변경했습니다.
- `tests/test_pipeline_runtime_schema.py`에 entry -> status -> snapshot roundtrip 테스트와 missing-key 허용 테스트를 추가했습니다.

## 검증
- `python3 -m py_compile pipeline_runtime/schema.py pipeline_runtime/supervisor.py watcher_core.py` 통과
- `python3 -m unittest tests.test_pipeline_runtime_schema` 통과 (`42 tests`)
- `python3 -m unittest tests.test_pipeline_runtime_supervisor tests.test_watcher_core` 통과 (`321 tests`)
- `git diff --check` 통과

## 남은 리스크
- 이번 slice는 `lane_surface.py`, `lane_catalog.py`, `role_routes.py` 등 handoff에서 제외한 모듈을 건드리지 않았습니다.
- snapshot helper는 기존 `active_control_*` JSON key shape를 유지하기 위한 read/write 경로 정리입니다. status schema version bump나 문서 변경은 이번 handoff 범위가 아니어서 하지 않았습니다.
- 작업 시작 전부터 `verify/4/22/2026-04-22-role-harness-pipeline-automation-handoff-verification.md`, `report/gemini/2026-04-22-post-cleanup-next-slice.md`, `work/4/22/2026-04-22-runtime-legacy-control-cleanup-closeout.md`가 dirty/untracked 상태였습니다. 라운드 중 `verify/4/22/2026-04-22-post-cleanup-launcher-automation-realignment.md`도 별도로 생겼지만 이번 implement slice에서는 건드리지 않았습니다.
