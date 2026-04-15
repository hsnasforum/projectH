# 2026-04-15 gate async cleanup fix

## 요약
- `scripts/pipeline_runtime_gate.py`의 `synthetic-soak` 종료 경로에서 성공 시 synthetic workspace를 메인 프로세스가 `shutil.rmtree()`로 직접 지우던 흐름을 제거했습니다.
- 종료 후 정리 때문에 gate 프로세스가 오래 붙잡히고 리포트 파일이 늦게 쓰이거나 아예 남지 않는 문제를 줄이기 위해, workspace 삭제를 백그라운드 비동기 정리로 바꿨습니다.
- 리포트 요약에는 `workspace_retained`와 `workspace_cleanup`를 함께 남겨 정리 요청 상태를 구분하도록 했습니다.

## 변경 파일
- `scripts/pipeline_runtime_gate.py`
- `tests/test_pipeline_runtime_gate.py`

## 핵심 변경
- `_schedule_workspace_cleanup()` 추가
  - detached subprocess로 synthetic workspace 삭제를 비동기로 요청합니다.
- `_finalize_synthetic_workspace()` 추가
  - `keep_workspace`, soak 성공 여부, background delete 요청 실패 여부를 한곳에서 결정합니다.
- `synthetic-soak` main 경로 변경
  - 성공한 synthetic run이라도 메인 프로세스가 직접 `rmtree()`를 돌며 report write를 늦추지 않도록 수정했습니다.
  - report summary에 cleanup 상태를 명시합니다.

## 배경
- 실제 24h synthetic soak에서 예정 종료 시각 이후 gate 프로세스가 오래 살아 있었고, 리포트가 즉시 남지 않았습니다.
- runtime 프로세스 정리와 별도로 synthetic workspace 후처리가 gate 종료를 붙잡는 경로가 취약점으로 확인되었습니다.

## 남은 메모
- 이번 라운드에서는 soak 재실행 없이 종료 경로만 단위 검증했습니다.
- 실제 24h 재게이트는 사용자 요청에 따라 진행하지 않았습니다.
