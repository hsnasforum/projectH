# Pipeline Runtime 구현 계획

작성일: 2026-04-11

## 목표
- `supervisor`를 runtime status/event/receipt의 단일 writer로 세웁니다.
- `controller`와 `pipeline_gui`는 `status.json` 또는 runtime HTTP API만 읽도록 전환합니다.
- `tmux`는 직접 관측 대상이 아니라 `TmuxAdapter` 뒤의 substrate로 격하합니다.
- `.pipeline/*.md + CONTROL_SEQ`는 계속 canonical control plane으로 유지합니다.

## 구현 축
- `pipeline_runtime/` 패키지 추가
- `start-pipeline.sh` / `stop-pipeline.sh` thin wrapper화
- watcher exporter production 경로 비활성화 지원
- controller runtime API canonical화
- pipeline_gui runtime status reader 전환
- run-scoped receipt/wrapper-events/status surface 정식화

## 기록 규칙
- 진행 기록: `report/pipeline_runtime/progress/`
- 검증 기록: `report/pipeline_runtime/verification/`
- cutover 판단 기록: `report/pipeline_runtime/cutover/`
- 이번 트랙에서는 `work/`를 사용하지 않습니다.
