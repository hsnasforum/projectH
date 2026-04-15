# 2026-04-11 Pipeline Runtime live gate harness 후속 진행

## 변경 요약
- `scripts/pipeline_runtime_gate.py`를 추가해 internal runtime live fault-check / soak sample 경로를 만들었습니다.
- `supervisor` status에 `degraded_reasons`를 추가해 복수 degraded 원인을 함께 노출하도록 보강했습니다.
- `pipeline_gui` setup 비동기 완료 후 `home` 모드에서도 detail snapshot으로 다시 수렴하도록 수정해 flaky한 `PreviewReady` / `Applied` downgrade를 막았습니다.

## 이번 라운드에서 확인한 것
- live fault check는 실제 `tmux` 세션 손실과 lane pid 강제 종료를 supervisor/runtime surface 기준으로 재현할 수 있습니다.
- stale historical `VERIFY_DONE`를 current run receipt 대상으로 잘못 주워오던 경로를 줄여 short soak sample이 `STARTING/RUNNING`으로 수렴하는 것을 확인했습니다.

## 남은 gate
- 6시간 mini soak
- 24시간 soak
- long soak에서 false READY / duplicate dispatch / missing receipt가 없는지 최종 확인
