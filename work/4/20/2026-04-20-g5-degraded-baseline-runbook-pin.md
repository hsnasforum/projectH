# 2026-04-20 g5 degraded baseline runbook pin

## 변경 파일
- `docs/projectH_pipeline_runtime_docs/05_운영_RUNBOOK.md`

## 사용 skill
- `finalize-lite`: docs-only 한 줄 truth-sync 라운드의 실제 검증 범위와 추가 doc-sync 필요 여부를 좁게 확인했습니다.
- `work-log-closeout`: projectH 표준 섹션 순서로 `/work` closeout을 남겼습니다.

## 변경 이유
- seq 581 handoff는 `docs/projectH_pipeline_runtime_docs/05_운영_RUNBOOK.md §3.5 현재 검증 원칙`의 현재 검증 원칙 문장에 thin-client/UI focused baseline인 `python3 -m unittest tests.test_pipeline_gui_backend` 46 green을 한 줄로 고정하라고 지정했습니다.
- 직전 docs-only 라운드에서 `docs/projectH_pipeline_runtime_docs/verify_queue/2026-04-20-dispatcher-trace-backfill.md`는 이미 materialize되었고, 이번 라운드는 그 queue 문서를 다시 건드리지 않은 채 AXIS-G5-DEGRADED-BASELINE 문장 pin만 clean reissue로 닫는 범위였습니다.

## 핵심 변경
- `docs/projectH_pipeline_runtime_docs/05_운영_RUNBOOK.md §3.5 현재 검증 원칙`의 `현재 기본 검증은 아래 세 축입니다.` 한 문장을 handoff가 지정한 replacement 문장으로 byte-for-byte 교체했습니다.
- 교체 문장은 thin-client/UI current-truth read-model 회귀의 focused baseline으로 `python3 -m unittest tests.test_pipeline_gui_backend` 46 green을 함께 유지한다고 명시합니다.
- `1. launcher live stability gate` / `2. incident replay` / `3. 실제 작업 세션` 목록과 그 아래 본문은 이번 라운드에서 추가 수정하지 않았습니다.
- production code, tests, 다른 docs, `.pipeline/*` control slot, `verify_queue/` 문서는 건드리지 않았습니다. `05_운영_RUNBOOK.md` 안의 기존 다른 dirty hunks도 그대로 두고 이번 one-sentence replacement만 추가했습니다.
- 오늘(2026-04-20) same-family docs-only round count는 1에서 2로 증가했습니다. 3+ same-day docs-only saturation threshold는 아직 아니지만, 다음 docs-only micro-slice는 해당 경계에 닿습니다.
- 이번 라운드 편집 범위상 seq 527 / 530 / 533 / 536 / 539 / 543 / 546 / 549 / 552 / 555 / 561 / 564 / 567 / 570 / 576 계약과 `.pipeline/operator_request.md` seq 521 canonical literals는 SUPERSEDES chain 558 -> 573 -> 579를 포함해 건드리지 않아 그대로 유지됩니다.

## 검증
- `python3 -m unittest tests.test_pipeline_gui_backend`
  - 결과: `Ran 46 tests in 0.092s`, `OK`
- `git diff --check -- "docs/projectH_pipeline_runtime_docs/05_운영_RUNBOOK.md"`
  - 결과: 출력 없음

## 남은 리스크
- AXIS-G5-DEGRADED-BASELINE은 focused thin-client baseline 문장으로 이제 shipped 상태이지만, 나머지 5개 tracked baseline(`tests.test_pipeline_runtime_supervisor` 101, `tests.test_pipeline_runtime_control_writers` 7, `tests.test_operator_request_schema` 6, `tests.test_pipeline_runtime_schema` 36, `tests.test_watcher_core` 143)은 이번 라운드에 의도적으로 묶지 않았습니다.
- AXIS-DISPATCHER-TRACE-BACKFILL-QUEUE-DOC은 seq 576 기준으로 materialized 상태를 유지합니다. handoff 기준 trigger는 이미 met(`.pipeline/runs/20260420T142213Z-p817639/`, 329 `dispatch_selection` events)로 pin되어 있지만, implement lane에서는 이를 재검증하지 않았고 실제 verification 실행은 verify-lane round가 남아 있습니다.
- AXIS-STALE-REFERENCE-AUDIT는 계속 closed 상태입니다.
- AXIS-EMIT-KEY-STABILITY-LOCK / AXIS-AUTONOMY-KEY-STABILITY-LOCK은 각각 seq 567 / seq 570 기준 shipped 상태를 유지합니다.
- 남은 code-axis 후보는 AXIS-G4(실제 stall trace 필요), AXIS-G6-TEST-WEB-APP(medium-high risk single-cell narrowing)입니다.
- G11, G8-pin, G3, G9, G10, G6-sub2, G6-sub3는 계속 deferred 상태입니다.
- unrelated `tests.test_web_app`의 `LocalOnlyHTTPServer` PermissionError 10건은 이번 범위 밖이라 그대로 열려 있습니다.
- 오늘(2026-04-20) docs-only round count는 이제 2입니다. 같은 family의 세 번째 docs-only micro-slice는 saturation rule 경계에 닿으므로 bundle 또는 escalation 판단이 필요합니다.
- dirty worktree 파일은 이번 one-sentence edit과 이 `/work` closeout 외에는 그대로 두었습니다.
