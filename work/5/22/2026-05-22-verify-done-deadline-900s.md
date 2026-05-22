# 2026-05-22 verify done deadline 900s

## 변경 파일
- `.pipeline/config/runtime_policy.json`
- `watcher_core.py`
- `work/5/22/2026-05-22-verify-done-deadline-900s.md`
- 기존 local 정렬 변경(이번 turn에서 추가 수정하지 않음):
  - `tests/test_watcher_core.py`

## 사용 skill
- `work-log-closeout`: 실제 변경 파일, 실행한 검증, 남은 리스크를 한국어 `/work` 기록으로 남기기 위해 사용했습니다.

## 변경 이유
- CONTROL_SEQ 2151에 따라 live Claude verify 처리 시간이 약 7분 3초로 확인된 상황에서 300초 verify done deadline이 먼저 만료되는 문제를 줄이기 위해 deadline을 900초로 늘렸습니다.
- 900초는 관찰된 처리 시간의 약 2배 여유를 두는 값입니다.

## 핵심 변경
- `.pipeline/config/runtime_policy.json`의 `verify_done_deadline_sec` 값을 `300`에서 `900`으로 변경했습니다.
- `watcher_core.py`의 `DEFAULT_VERIFY_DONE_DEADLINE_SEC` 값을 `300.0`에서 `900.0`으로 변경했습니다.
- `tests/test_watcher_core.py`의 기존 기본 deadline 회귀 테스트는 현재 900초 기대값으로 정렬되어 있음을 확인했습니다. 이번 turn에서는 테스트 파일을 추가 수정하지 않았습니다.
- `verify/` note, `.pipeline/` control slot, commit, push, branch/PR publish, merge, release, publication은 실행하지 않았습니다.

## 검증
- 통과: `python3 -c "import json; d=json.load(open('.pipeline/config/runtime_policy.json')); assert d['verify_done_deadline_sec']==900, d; print('policy OK')"`
  - 결과: `policy OK`
- 통과: `python3 -c "import watcher_core; assert watcher_core.DEFAULT_VERIFY_DONE_DEADLINE_SEC==900.0; print('default OK')"`
  - 결과: `default OK`
- 통과: `python3 -m py_compile watcher_core.py`
  - 결과: PASS, 출력 없음
- 통과: `python3 -m unittest tests.test_pipeline_runtime_cli tests.test_pipeline_runtime_supervisor tests.test_watcher_core 2>&1 | tail -5`
  - 결과: `Ran 548 tests in 11.342s`, `OK`
- 통과: `git diff --check -- watcher_core.py .pipeline/config/runtime_policy.json tests/test_watcher_core.py work/5/22/2026-05-22-verify-done-deadline-900s.md`
  - 결과: PASS, 출력 없음

## 남은 리스크
- CONTROL_SEQ 2151의 지정 checks와 548개 전체 suite는 통과했습니다.
- 이번 slice는 deadline 값을 늘리는 로컬 변경이며, 파이프라인 재시작이나 live Claude trigger 재관찰은 실행하지 않았습니다.
- `pipeline_runtime/supervisor.py`의 runtime policy 전달 경로는 기존 2149/이전 slice 변경을 그대로 사용하며 이번 slice에서 추가 수정하지 않았습니다.
