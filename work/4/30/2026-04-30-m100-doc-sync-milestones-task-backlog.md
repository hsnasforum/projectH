# 2026-04-30 M100 doc-sync MILESTONES/TASK_BACKLOG

## 변경 파일

- `docs/MILESTONES.md` — M99 advisory-loop-recovery-guard 항목 추가, `Next 3 Implementation Priorities`를 PR #91/#92 merge backlog + M100 advisory pending + 장기 방향으로 갱신
- `docs/TASK_BACKLOG.md` — `next phase target` Remaining에 M99 advisory-loop-recovery-guard 기록 추가
- `work/4/30/2026-04-30-m100-doc-sync-milestones-task-backlog.md` — 이번 closeout

## 사용 skill

- `work-log-closeout` — `/work` closeout 필수 섹션, 실제 검증 기록, 남은 리스크 형식을 맞추기 위해 사용

## 변경 이유

- `.pipeline/implement_handoff.md` CONTROL_SEQ 1450이 M100 docs-only sync를 지시했다.
- `docs/MILESTONES.md`의 `Next 3 Implementation Priorities`가 오래된 PR #71-#86/M98 후속 상태를 가리키고 있었고, `docs/TASK_BACKLOG.md`의 Remaining에는 M99 publish 이후 항목이 아직 반영되지 않았다.

## 핵심 변경

- `docs/MILESTONES.md`의 `## M98 교정 이력 상세 조회` 바로 뒤에 `## M99 advisory-loop-recovery-guard (watcher runtime)` 섹션을 추가했다.
- M99 항목에 `DEFAULT_ADVISORY_RECOVERY_SEC`, `_get_next_control_seq()` monotonicity, advisory prompt broad-read guard, root memory/harness/pipeline README sync, regression test 3개, commit `9331c5b`, branch, PR #92 정보를 기록했다.
- `## Next 3 Implementation Priorities`를 PR #91/#92 draft merge backlog, M100 advisory pending/local doc-sync, 장기 cross-session memory 방향으로 교체했다.
- `docs/TASK_BACKLOG.md`의 `next phase target` Remaining 끝에 M99 advisory-loop-recovery-guard를 추가했다.
- 코드 파일은 수정하지 않았다.

## 검증

- `sha256sum .pipeline/implement_handoff.md` — PASS, `e27566ffe7e9088bbccdda1c4b4f30e20ca83ae71e8652280c3b8c19c571bb58`
- `git diff --check -- docs/MILESTONES.md docs/TASK_BACKLOG.md` — PASS
- `rg -n "M99 advisory-loop-recovery-guard|PR #91|PR #92|M100 방향|broader cross-session" docs/MILESTONES.md docs/TASK_BACKLOG.md` — PASS, M99/PR #91/#92/M100 방향/TASK_BACKLOG Remaining 기록 확인
- `python3 -m py_compile` — 미실행, docs-only handoff라 불필요

## 남은 리스크

- 광범위 unittest, Playwright E2E, 장시간 soak는 docs-only handoff 범위가 아니어서 실행하지 않았다.
- PR #91 (M98)과 PR #92 (M99)는 여전히 draft 및 `pr_merge_gate` operator 승인 대기 상태로 문서에 기록했다.
- commit, push, PR publish는 implement role 제약에 따라 수행하지 않았다.
