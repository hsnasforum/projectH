# 2026-04-20 g5 degraded baseline runbook pin verification

## 변경 파일
- `verify/4/20/2026-04-20-g5-degraded-baseline-runbook-pin-verification.md`

## 사용 skill
- `round-handoff`: seq 581 one-sentence docs-only 슬라이스(AXIS-G5-DEGRADED-BASELINE) 구현 주장을 실제 HEAD/파일/테스트에 narrowest로 재대조하고, docs-only scope에 맞춰 `tests.test_pipeline_gui_backend`와 `git diff --check`만 재실행했습니다.

## 변경 이유
- 새 `/work`(`work/4/20/2026-04-20-g5-degraded-baseline-runbook-pin.md`)가 seq 581의 pin 그대로 `docs/projectH_pipeline_runtime_docs/05_운영_RUNBOOK.md §3.5 현재 검증 원칙`의 한 문장을 교체했다고 주장했습니다. SCOPE_HINT가 docs-only로 감지했으므로 verify 라인은 (a) 해당 line이 handoff의 REPLACEMENT 문장과 byte-exact 일치하는지, (b) 나머지 섹션 본문과 다른 docs 파일이 이번 라운드에서 추가 수정되지 않았는지, (c) `tests.test_pipeline_gui_backend` 46 green과 `git diff --check` clean이 실제 재현되는지, (d) seq 576 materialize한 `verify_queue/2026-04-20-dispatcher-trace-backfill.md`가 이번 라운드에서 건드려지지 않았는지, (e) 오늘 docs-only round count가 1 → 2로 움직였는지만 확인하면 충분했습니다.

## 핵심 변경 (verify 관점 스냅샷)
- `docs/projectH_pipeline_runtime_docs/05_운영_RUNBOOK.md` line 74가 handoff REPLACEMENT 문장과 byte-exact 일치함을 `rg` 단일 히트로 확인:
  `현재 기본 검증은 아래 세 축이며, thin-client/UI current-truth read-model 회귀의 focused baseline으로 \`python3 -m unittest tests.test_pipeline_gui_backend\` 46 green을 함께 유지합니다.`
- `§3.5` 아래 `1. launcher live stability gate` / `2. incident replay` / `3. 실제 작업 세션` enumerated list와 그 뒤의 long-soak / synthetic-soak 본문은 byte-for-byte 유지(직전 Read에서 확인한 구조 그대로).
- `git diff --stat -- docs/projectH_pipeline_runtime_docs/05_운영_RUNBOOK.md` 결과: `13 insertions(+), 11 deletions(-)` (1 file changed). 이번 라운드 직접 편집 1줄 외에도 dirty worktree 잔여 수정이 남아 있지만 handoff가 "05_운영_RUNBOOK.md 안의 기존 다른 dirty hunks도 그대로 둔다"고 허용한 범위. `git diff --check` output 없음 (trailing whitespace / CR-LF 이슈 없음).
- `docs/projectH_pipeline_runtime_docs/verify_queue/`는 여전히 단일 엔트리 `2026-04-20-dispatcher-trace-backfill.md`만 untracked 상태로 보유 — 이번 라운드에서 추가 생성/수정 없음.
- `docs/projectH_pipeline_runtime_docs/` 아래 dirty 목록은 `01_`, `03_`, `04_`, `05_`, `06_` 5개 파일로 직전 라운드 이전 상태와 동일(이번 편집으로 추가/변경된 파일 없음).
- production code, tests, `.pipeline/*` control 파일은 이번 라운드 수정 없음. seq 527 / 530 / 533 / 536 / 539 / 543 / 546 / 549 / 552 / 555 / 561 / 564 / 567 / 570 / 576 shipped surface 전부 byte-for-byte 유지. `.pipeline/operator_request.md` seq 521 canonical literals는 seq 558 → 573 → 579 SUPERSEDES chain으로 계속 보존.

## 검증
- `python3 -m unittest tests.test_pipeline_gui_backend` → `Ran 46 tests in 0.063s`, `OK` (verify 라인 재실행 결과; /work가 기록한 46 green과 정합).
- `git diff --check -- "docs/projectH_pipeline_runtime_docs/05_운영_RUNBOOK.md"` → 출력 없음 (verify 라인 재실행 결과).
- `rg -n '현재 기본 검증은' docs/projectH_pipeline_runtime_docs/05_운영_RUNBOOK.md` → line 74 단일 히트, 내용은 REPLACEMENT 문장과 byte-exact.
- `git diff --stat -- "docs/projectH_pipeline_runtime_docs/05_운영_RUNBOOK.md"` → 1 file changed, 13 insertions(+), 11 deletions(-). one-sentence replacement + 기존 dirty hunks 유지가 반영된 수치.
- `git status --short -- docs/projectH_pipeline_runtime_docs/` → 넘버링 파일 5개(M 01/03/04/05/06) + untracked `verify_queue/`. 이번 라운드 범위 밖 dirty는 그대로 유지.
- 실행하지 않은 항목 (명시):
  - `tests.test_pipeline_runtime_supervisor` (101), `tests.test_pipeline_runtime_control_writers` (7), `tests.test_operator_request_schema` (6), `tests.test_pipeline_runtime_schema` (36), `tests.test_watcher_core` (143): docs-only scope라 의도적 생략. /work가 직전 baseline 수치를 인용하고 있고 이번 라운드는 python 모듈이나 contract를 건드리지 않음.
  - `tests.test_web_app`, Playwright, `make e2e-test`: browser/e2e 계약 변경 없음. 의도적 생략.
  - full-repo dirty worktree audit: 범위 밖.
- `.claude/rules/doc-sync.md` 관점 점검: 이번 one-sentence pin은 이미 shipped된 seq 567 thin-client baseline을 참조하므로 "implementation truth를 따르지 않는 wishful future behavior" 아님. TODO/OPEN QUESTION 마킹 불필요. mirrored agent/skill/config 동반 sync 요구 없음. plandoc/ 범위도 아님.

## 남은 리스크
- **AXIS-G5-DEGRADED-BASELINE shipped**: focused thin-client baseline 문장으로 §3.5에 byte-exact 고정. 나머지 5개 tracked baseline(supervisor 101 / control_writers 7 / operator_request_schema 6 / schema 36 / watcher_core 143)은 의도적으로 silent 유지.
- **AXIS-DISPATCHER-TRACE-BACKFILL**: queue doc은 seq 576으로 materialized 상태 유지. trigger(>=2 `dispatch_selection`)는 `.pipeline/runs/20260420T142213Z-p817639/` 기준 329회로 이미 met이며, 실제 verification 실행(target note `verify/4/20/2026-04-20-dispatcher-trace-backfill-verification.md`)은 verify-lane 별도 라운드로 남음.
- **AXIS-STALE-REFERENCE-AUDIT**: closed 유지.
- **AXIS-EMIT-KEY-STABILITY-LOCK**(seq 567) / **AXIS-AUTONOMY-KEY-STABILITY-LOCK**(seq 570): 계속 shipped.
- **코드 후보**: AXIS-G4(실제 stall trace 필요, 핀 불충분), AXIS-G6-TEST-WEB-APP(medium-high risk single-cell narrowing).
- **G11, G8-pin, G3, G9, G10, G6-sub2, G6-sub3**: 계속 deferred.
- **`tests.test_web_app`** 10건 `LocalOnlyHTTPServer` PermissionError baseline 유지.
- **Docs-only round count**: 오늘(2026-04-20) 1 → 2. 3+ saturation threshold 바로 다음 라운드 경계. 같은 family의 또 다른 narrower docs-only micro-slice는 기본 제안으로 올리지 않음.
- **Dirty worktree**: broad unrelated dirty 파일 + `docs/projectH_pipeline_runtime_docs/` 내 5개 파일 수정 + `pipeline_runtime/schema.py:22-25` pre-existing label-rename diff 등 기존 상태 그대로. 이번 verify가 추가 stage / reset 하지 않음.
- **next slice ambiguity → Gemini-first**: 남은 후보는 축이 서로 다르고 current-risk reduction이 명확하지 않음.
  - (A) verify-lane이 queued AXIS-DISPATCHER-TRACE-BACKFILL을 실제 실행하는 verify 라운드(implement slice 아님, 별도 verify round)
  - (B) AXIS-G4 stall trace pin (핀 불충분 → Gemini 보강 필요)
  - (C) AXIS-G6-TEST-WEB-APP 단일 test method 좁히기 (medium-high risk)
  - (D) 다른 docs-only micro-slice (saturation 경계 접근, 기본 제안 금지)
  real operator-only blocker 없음. 따라서 seq 582 next-control은 `.pipeline/operator_request.md`가 아니라 `.pipeline/gemini_request.md`로 여는 것이 맞습니다.
