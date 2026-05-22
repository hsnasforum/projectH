# 2026-05-22 Claude verify lane precondition ready

## 변경 파일
- `work/5/22/2026-05-22-claude-verify-lane-precondition-ready.md`

## 사용 skill
- `work-log-closeout`: 실제 변경 파일, 실행한 검증, 미실행 범위, 남은 리스크를 한국어 `/work` 기록으로 남기기 위해 사용했습니다.

## 변경 이유
- CONTROL_SEQ 2141에 따라 live Claude verify 관찰을 시작하기 전 로컬 전제가 충족됐는지 한 장의 운영 기록으로 고정했습니다.
- advisory가 제안한 child-exit/PTY EOF 추가 테스트는 `cli.py:1596`의 `_finish_stream_once()` 호출 경로가 이미 존재하므로 이번 blocking 갭으로 보지 않았습니다.
- 실제 목표는 파이프라인 재시작 후 trigger-5가 Claude verify lane으로 전달되고 `TASK_DONE source=wrapper lane=Claude`가 발생하는지 관찰하는 것입니다.

## 전제 점검표
| 전제 | 상태 |
|---|---|
| wrapper `finish_stream()` -> `TASK_DONE` 발행, text/jsonl mode | READY, CONTROL_SEQ 2132 |
| `stop_requested` 경로 `_finish_stream_once()` 호출 | READY, CONTROL_SEQ 2132 |
| real `_WrapperEmitter` SIGTERM replay | READY, CONTROL_SEQ 2133 |
| `verify_done_deadline_sec=300s` 적용 | READY, CONTROL_SEQ 2129 working tree |
| Claude verify lane profile 활성화 | READY, CONTROL_SEQ 2137 |
| trigger-5 fresh verify 대상 생성 | READY, CONTROL_SEQ 2137 |

## 검증
- 통과: `git diff --check -- work/5/22/2026-05-22-claude-verify-lane-precondition-ready.md`
- 미실행: 소스 코드와 테스트 파일을 변경하지 않아 단위 테스트, broad runtime smoke, browser/E2E는 실행하지 않았습니다.

## 남은 리스크
- 이번 slice는 전제 점검 기록만 추가했으며, 제품/런타임 소스 코드, 테스트, `verify/`, `.pipeline/` 파일은 변경하지 않았습니다.
- commit, push, PR 생성, merge, release, publication은 실행하지 않았습니다.
- 다음 단계는 파이프라인 재시작 후 trigger-5 dispatch와 `TASK_DONE source=wrapper lane=Claude` 발생 여부를 새 `events.jsonl`에서 확인하는 것입니다.
- Claude가 `TASK_ACCEPTED` 이후 300초 안에 `TASK_DONE`을 내지 못하면 `claude-print-jsonl-pipe` 종료/`finish_stream()` 경로를 별도 slice로 다뤄야 합니다.
