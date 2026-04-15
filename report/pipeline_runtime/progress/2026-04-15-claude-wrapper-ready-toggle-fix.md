## 변경 파일
- pipeline_runtime/cli.py
- tests/test_pipeline_runtime_cli.py

## 사용 skill
- 없음

## 변경 이유
- Claude implement lane이 작업 중 `READY -> WORKING -> READY`를 반복했습니다.
- 로그 확인 결과, Codex 때와 같은 계열로 `task_hint`가 아직 active인데 wrapper가 prompt 재등장만 보고 `TASK_DONE/READY`를 찍는 문제가 다시 나타났습니다.

## 핵심 변경
- wrapper 종료 조건을 `prompt_visible` 단독 기준에서 `현재 accepted task의 task_hint가 inactive로 전환된 뒤 ready가 확인될 때` 기준으로 강화했습니다.
- accepted task가 아직 active면 prompt가 다시 보여도 `TASK_DONE`를 emit하지 않도록 바꿨습니다.
- `TASK_DONE`는 `last_activity_at`와 `task_inactive_since` 모두 settle window를 지난 뒤에만 emit되도록 조정했습니다.
- 회귀 테스트를 task_hint active 유지 중에는 `TASK_DONE`가 나오지 않고, inactive 전환 후 settle 뒤에만 `TASK_DONE`가 나오도록 갱신했습니다.

## 검증
- `python3 -m py_compile pipeline_runtime/cli.py tests/test_pipeline_runtime_cli.py pipeline_runtime/supervisor.py tests/test_pipeline_runtime_supervisor.py`
- `python3 -m unittest -v tests.test_pipeline_runtime_cli`
- `python3 -m unittest -v tests.test_pipeline_runtime_supervisor`
- `python3 -m pipeline_runtime.cli restart /home/xpdlqj/code/projectH --mode experimental --session aip-projectH --no-attach`
- live 확인:
  - run `20260415T085315Z-p2721886`
  - Claude wrapper: `TASK_ACCEPTED` 후 40초 이상 `TASK_DONE/READY` 재발 없음
  - supervisor status: Claude `WORKING`, note `seq 136`

## 남은 리스크
- 현재 implement lane task hint는 closed verify job의 `job_id`를 재사용합니다. 이번 수정으로 false `READY`는 막았지만, implement lane 전용 task identity를 더 분리하면 해석이 더 명확해질 수 있습니다.
- compat/debug surface의 legacy helper 잔존 자체는 이번 수정 범위 밖입니다.
