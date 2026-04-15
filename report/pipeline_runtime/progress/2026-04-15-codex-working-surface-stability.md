## 변경 파일
- pipeline_runtime/supervisor.py
- tests/test_pipeline_runtime_supervisor.py

## 사용 skill
- 없음

## 변경 이유
- Codex verify lane이 실제로 `VERIFY_RUNNING`인 동안 wrapper가 잠깐 `READY`를 찍으면 launcher/controller가 `WORKING -> READY -> WORKING`으로 흔들렸습니다.
- 운영 화면에서는 active verify round가 열려 있으면 false `READY`보다 runtime round truth를 우선해야 합니다.

## 핵심 변경
- `RuntimeSupervisor._lane_should_surface_working()`를 추가했습니다.
- active lane이 현재 active round를 들고 있고 round state가 `VERIFY_PENDING` 또는 `VERIFYING`이면, wrapper가 잠깐 `READY`를 보내도 supervisor surface는 `WORKING`을 유지하도록 접었습니다.
- forced-working 상황에서 note가 비었거나 `prompt_visible`이면 `verifying` 같은 round note로 바꿔 launcher/controller 표시가 덜 혼란스럽게 했습니다.
- `tests.test_pipeline_runtime_supervisor`에 active verify round 중 wrapper `READY`를 `WORKING`으로 surface하는 회귀 테스트를 추가했습니다.

## 검증
- `python3 -m py_compile pipeline_runtime/supervisor.py tests/test_pipeline_runtime_supervisor.py`
- `python3 -m unittest -v tests.test_pipeline_runtime_supervisor`

## 남은 리스크
- wrapper 자체는 여전히 Codex UI의 `prompt_visible`을 낙관적으로 해석할 수 있습니다. 이번 수정은 supervisor surface를 안정화하는 1차 방어선입니다.
- 현재 실행 중인 supervisor 프로세스에는 재시작 전까지 이 수정이 반영되지 않습니다.
