# 2026-04-21 operator retriage semantic bump

## 변경 파일
- `pipeline_runtime/operator_autonomy.py`
- `pipeline_runtime/supervisor.py`
- `watcher_core.py`
- `tests/test_pipeline_runtime_supervisor.py`
- `tests/test_watcher_core.py`
- `.pipeline/README.md`
- `docs/projectH_pipeline_runtime_docs/03_기술설계_명세서.md`
- `docs/projectH_pipeline_runtime_docs/05_운영_RUNBOOK.md`
- `work/4/21/2026-04-21-operator-retriage-semantic-bump.md` (새 파일)

## 사용 skill
- `security-gate`: operator stop publish/gate와 watcher routing에 영향을 주는 변경이라, 새 삭제/덮어쓰기/외부 publish/credential 동작을 만들지 않는지 확인했습니다.
- `doc-sync`: runtime contract가 바뀐 내용을 `.pipeline/README.md`와 runtime docs에 맞췄습니다.
- `work-log-closeout`: 변경 파일, 검증, 남은 리스크를 표준 `/work` 형식으로 정리했습니다.

## 변경 이유
- operator retriage follow-up이 규칙대로 더 높은 `CONTROL_SEQ`의 `.pipeline/operator_request.md`를 다시 쓰면, 기존 로직은 seq/mtime 변경을 새 사건으로 보아 24시간 suppress window와 `operator_retriage_no_next_control` age를 리셋했습니다.
- 그 결과 verify/handoff owner가 같은 결정을 반복 기록할수록 watcher가 다시 retriage를 보내고, advisory escalation 조건이 계속 밀리는 루프가 생겼습니다.

## 핵심 변경
- `classify_operator_candidate(...)`에 `first_seen_ts` override를 추가하고, semantic fingerprint에서 `STATUS`, `CONTROL_SEQ`, `SOURCE`, `SUPERSEDES`, timestamp류 header와 `control_seq` 값을 제외했습니다.
- supervisor는 같은 semantic fingerprint가 autonomy state에 남아 있으면 persisted `first_seen_at`을 재사용해 suppress deadline이 seq-only bump로 연장되지 않게 했습니다.
- watcher는 operator retriage fingerprint와 시작 시각을 별도로 기억합니다. 같은 fingerprint의 operator_request seq-only bump는 새 notify/turn transition을 만들지 않고 signature만 갱신하며, `operator_retriage_no_next_control` age는 기존 시작 시각을 이어갑니다.
- 같은 의미의 seq-only bump가 suppress/retriage age를 리셋하지 않는다는 계약을 `.pipeline/README.md`, runtime 기술설계, 운영 RUNBOOK에 기록했습니다.
- 회귀 테스트를 추가했습니다.
  - classifier가 seq-only bump에서 같은 fingerprint/suppress deadline을 유지하는지.
  - supervisor가 persisted first_seen을 보존하는지.
  - watcher가 seq-only bump 후에도 기존 retriage age로 advisory escalation을 진행하는지.

## 검증
- `python3 -m py_compile pipeline_runtime/operator_autonomy.py pipeline_runtime/supervisor.py watcher_core.py`
  - 출력 없음, `rc=0`
- `python3 -m unittest tests.test_pipeline_runtime_supervisor.RuntimeSupervisorTest.test_classify_operator_candidate_seq_only_bump_keeps_semantic_fingerprint tests.test_pipeline_runtime_supervisor.RuntimeSupervisorTest.test_write_status_preserves_operator_gate_first_seen_across_seq_only_bump`
  - `Ran 2 tests in 0.020s`
  - `OK`
- `python3 -m unittest tests.test_watcher_core.RollingSignalTransitionTest.test_operator_retriage_seq_only_bump_preserves_no_next_control_age`
  - `Ran 1 test in 0.024s`
  - `OK`
- `python3 -m unittest tests.test_pipeline_runtime_supervisor`
  - `Ran 119 tests in 1.123s`
  - `OK`
- `python3 -m unittest tests.test_watcher_core`
  - `Ran 160 tests in 8.069s`
  - `OK`
- `python3 -m unittest tests.test_operator_request_schema`
  - `Ran 9 tests in 0.001s`
  - `OK`
- `git diff --check -- pipeline_runtime/operator_autonomy.py pipeline_runtime/supervisor.py watcher_core.py tests/test_pipeline_runtime_supervisor.py tests/test_watcher_core.py .pipeline/README.md docs/projectH_pipeline_runtime_docs/03_기술설계_명세서.md docs/projectH_pipeline_runtime_docs/05_운영_RUNBOOK.md`
  - 출력 없음, `rc=0`

## 남은 리스크
- live watcher 재시작/실운영 smoke는 수행하지 않았습니다. 이번 검증은 replay/unit 중심입니다.
- watcher retriage 시작 시각은 프로세스 메모리 기준입니다. watcher 재시작은 기존 루프 자체를 끊는 운영 수단이라, 이번 slice에서는 restart 이후 age 복원까지 확장하지 않았습니다.
- semantic fingerprint는 동일 decision/body를 기준으로 유지됩니다. `DECISION_REQUIRED`, `BASED_ON_WORK`, 본문 의미가 바뀌면 새 operator candidate로 취급하는 것이 의도입니다.
