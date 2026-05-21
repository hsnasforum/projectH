# 2026-05-20 idle active verify round runtime doc sync

## 변경 파일

- `.pipeline/README.md`
- `docs/projectH_pipeline_runtime_docs/03_기술설계_명세서.md`
- `docs/projectH_pipeline_runtime_docs/05_운영_RUNBOOK.md`
- `work/5/20/2026-05-20-idle-active-verify-round-runtime-doc-sync.md`

## 사용 skill

- `doc-sync`: 검증된 runtime status surface 동작을 운영/설계 문서에 맞추기 위해 사용했습니다.
- `work-log-closeout`: implement 라운드 closeout을 한국어 `/work` 기록으로 남기기 위해 사용했습니다.

## 변경 이유

handoff `CONTROL_SEQ: 1997`은 문서 전용 runtime contract sync를 요구했습니다. 직전 구현/검증에서 `turn_state=IDLE`이더라도 current `active_round.state`가 `VERIFY_PENDING` 또는 `VERIFYING`이면 verify work가 아직 살아 있으므로 non-degraded 상태에서 `ok/continue`로 숨기지 않고 `recovering/dispatch_stall/retrying`으로 표면화해야 한다는 동작이 확인되었습니다.

## 핵심 변경

- `.pipeline/README.md`에 public status가 `turn_state=IDLE`이어도 active verify round가 있으면 plain `ok/continue`가 아니며 launcher health가 `recovering`, `dispatch_stall`, `retrying`으로 보여야 한다는 규칙을 추가했습니다.
- `docs/projectH_pipeline_runtime_docs/03_기술설계_명세서.md`에 current `active_round.state=VERIFY_PENDING|VERIFYING`을 `turn_state=IDLE`만으로 완료 처리하지 않는 설계 규칙을 추가했습니다.
- `docs/projectH_pipeline_runtime_docs/05_운영_RUNBOOK.md`에 운영자가 이 상태 조합을 정상 완료가 아닌 active verify surface로 해석해야 하며 `ok + continue` 표시는 회귀라는 점을 추가했습니다.
- 이 라운드는 문서 동기화만 수행했습니다. Python source/test, advisory/operator control, commit/push/PR 작업은 변경하지 않았습니다.

## 검증

- `sha256sum .pipeline/implement_handoff.md`
  - PASS: `3da9542629d30631d5388c869a5f8463fb6b3d525de46b53238db1c1fa325d82`
- `git diff --check -- .pipeline/README.md docs/projectH_pipeline_runtime_docs/03_기술설계_명세서.md docs/projectH_pipeline_runtime_docs/05_운영_RUNBOOK.md`
  - PASS
- `rg -n "turn_state=IDLE.*active_round|active_round\\.state.*VERIFY_PENDING|recovering.*dispatch_stall.*retrying|ok/continue|ok \\+ continue" .pipeline/README.md docs/projectH_pipeline_runtime_docs/03_기술설계_명세서.md docs/projectH_pipeline_runtime_docs/05_운영_RUNBOOK.md`
  - PASS: `.pipeline/README.md:128`, `docs/projectH_pipeline_runtime_docs/03_기술설계_명세서.md:225`, `docs/projectH_pipeline_runtime_docs/05_운영_RUNBOOK.md:250`에서 새 contract 문구를 확인했습니다.

## 남은 리스크

- 문서 전용 sync라 이 라운드에서는 Python unit, Playwright/e2e, full smoke를 실행하지 않았습니다.
- 대상 runtime docs에는 이 라운드 이전의 미커밋 변경이 이미 있었고, 이번 라운드는 active verify round status-surface 문구만 추가했습니다.
- 넓은 문서 전체 감사는 수행하지 않았습니다.
