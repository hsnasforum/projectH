# 2026-04-15 active lane auth failure surfacing verification

## 요약
- 목표: active lane auth/login failure가 `READY`처럼 오인되지 않고 `BROKEN/DEGRADED`로 surface되는지 검증

## 실행한 검증
- `python3 -m py_compile pipeline_runtime/supervisor.py tests/test_pipeline_runtime_supervisor.py`
- `python3 -m unittest -v tests.test_pipeline_runtime_supervisor`
- `git diff --check -- pipeline_runtime/supervisor.py tests/test_pipeline_runtime_supervisor.py`

## 결과
- `py_compile` 통과
- `tests.test_pipeline_runtime_supervisor` 32건 통과
- diff whitespace 문제 없음

## 확인한 포인트
- active lane pane tail에서 `401 /login` 계열이 보이면 lane state가 `BROKEN`으로 내려감
- lane note가 `auth_login_required`로 기록됨
- runtime state가 `DEGRADED`로 전이됨
- auth failure일 때 automatic restart가 실행되지 않음

## 남은 리스크
- 현재는 active lane pane tail 기반 감지이므로, wrapper live event가 완전히 공식화되면 같은 failure를 wrapper `BROKEN` event로 더 아래 레이어에서 올리는 정리가 남아 있습니다.
