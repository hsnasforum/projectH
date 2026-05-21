# verify: 2026-05-21 pipeline launcher Task 4-C/D race condition

## 대상 work
`work/5/21/2026-05-21-pipeline-launcher-task4cd-race-condition.md`

## 검증 결과: READY — 18개 이슈 전체 완료

## 재실행 검증

| 검사 | 결과 |
|---|---|
| `py_compile` cli.py / supervisor.py | PASS |
| `unittest` cli + supervisor 226개 테스트 | PASS (1.069s) |
| `git diff --check` 변경 파일 | PASS |

## 수정 확인 (코드 직접 열람)

| ID | 위치 | 내용 | 확인 |
|---|---|---|---|
| P5 | cli.py:756–765 | `.supervisor-start.lock` `LOCK_EX\|LOCK_NB` — `BlockingIOError` 시 0 반환 | ✓ |
| P5 | cli.py:818–825 | `finally: LOCK_UN → close(lock_fd)` 정리 | ✓ |
| P5 | cli.py:759–762 | `open` 실패 시 `lock_fd = -1` → 잠금 없이 기존 경로 진행 | ✓ |
| P7 | supervisor.py:251–252 | fingerprint 검증 후 `_live_experimental_watcher_pid() != watcher_pid` 재확인 | ✓ |

## 확인하지 않은 항목

- Playwright / E2E / controller-smoke: UI 계약 미변경
- live runtime start/stop: flock 동작은 테스트에서 직접 `BlockingIOError` assert로 확인

## 전체 18개 이슈 완료 현황

| 라운드 | 완료 이슈 | 내용 |
|---|---|---|
| Task 1 | P6/P9/P10/P14/P15/P17 | 단순 버그 6건 |
| Task 4-A/B | P1/P2 | raw.jsonl 보존, events.jsonl 중복 억제 |
| Task 2 | P8/P11/P13/P16/P18 | 로직 교정 5건 |
| Task 3 | P3/P4 | SHA/raw.jsonl 캐싱 |
| Task 4-C/D | P5/P7 | 동시 start 직렬화, TOCTOU 재확인 |

## 남은 리스크

- 전체 18개 이슈 코드 수정 완료. commit/push/PR/merge/publish는 수행하지 않았음.
- dirty worktree 상태 유지 중 — 연관 파일들을 한 번에 검토 후 publish 결정 필요.
- Playwright / E2E / live runtime 검증은 이번 계획서 범위 밖으로 미실행.
  publish 전에 별도 smoke 라운드 권장.

## 다음 슬라이스 권고

**publish 번들 검토 또는 smoke 라운드.**
18개 이슈가 5개 라운드에 걸쳐 dirty worktree에 쌓여 있다.
PUBLISH_HELD 해제 전에 `git diff --stat` 전체 확인 후 commit 번들 구성 또는
operator 결정이 필요하다.
