# 2026-04-26 start-server hardening doc closure

## 변경 파일
- `e2e/start-server.sh`
- `docs/MILESTONES.md`
- `work/4/26/2026-04-26-start-server-hardening-doc-closure.md`

## 사용 skill
- `doc-sync`: M38 Axis 1 완료 사실과 Axis 2 범위를 `docs/MILESTONES.md`의 현재 milestone note에 맞췄습니다.
- `finalize-lite`: 변경 파일, 실행 검증, 미실행 범위, closeout 필요 여부를 점검했습니다.
- `work-log-closeout`: 실제 변경과 검증 결과를 이 `/work` closeout으로 정리했습니다.

## 변경 이유
- `e2e/start-server.sh`가 `set -u`만 사용해 중간 실패를 더 엄격하게 중단하지 못했고, `set -e` 추가 시 서버 조기 종료 경로의 `wait` 실패가 메시지를 생략할 수 있었습니다.
- `docs/MILESTONES.md`의 M38 note가 아직 방향 확정 대기 상태로 남아 있어, Axis 1 완료와 Axis 2 하드닝/doc closure 범위를 현재 사실에 맞춰 닫아야 했습니다.

## 핵심 변경
- `e2e/start-server.sh`에 `set -e`를 추가해 wrapper 중간 실패를 즉시 실패로 전파하도록 했습니다.
- 서버가 healthcheck 전에 종료되는 경로에서 `wait` exit code를 guard한 뒤 `[e2e] app.web server exited before becoming healthy (exit N)` 메시지가 남도록 했습니다.
- `docs/MILESTONES.md`의 M38 direction note를 Axis 1 완료 / Axis 2 진행 상태로 갱신했습니다.
- `Next 3 Implementation Priorities` 구조가 3개 항목을 유지하도록 M38 Axis 1/2 내용을 한 항목에 정리했습니다.

## 검증
- `bash -n e2e/start-server.sh`
  - 통과, 출력 없음.
- `git diff --check -- e2e/start-server.sh docs/MILESTONES.md`
  - 통과, 출력 없음.
- `python3 -m unittest -v tests.test_docs_sync`
  - 통과.
  - `Ran 13 tests in 0.043s`
- `e2e/start-server.sh true`
  - 현재 sandbox의 socket 제한으로 `python3 -m app.web`가 `PermissionError: [Errno 1] Operation not permitted`로 종료되는 조기 실패 경로를 확인했습니다.
  - wrapper가 개선된 메시지 `[e2e] app.web server exited before becoming healthy (exit 1)`를 출력했습니다.

## 남은 리스크
- 이번 handoff 범위는 wrapper hardening과 milestone closure라 전체 `make e2e-test`는 다시 실행하지 않았습니다. 직전 Axis 1 구현/검증에서 auto-start 경로 `150 passed`가 확인된 상태입니다.
- existing-server 재사용 경로 full E2E는 여전히 현재 sandbox의 socket 제한 때문에 이 round에서도 재검증하지 않았습니다.
- 작업 전부터 있던 `verify/4/25/2026-04-25-m36-preference-pause-functional-e2e.md`, `report/gemini/**`, 기존 미추적 `work/4/25/2026-04-25-m31-bundle-publish-closeout.md` 등은 이번 범위가 아니라 건드리지 않았습니다.
- commit, push, branch/PR 생성, 다음 slice 선택은 수행하지 않았습니다.
