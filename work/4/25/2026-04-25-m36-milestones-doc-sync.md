# 2026-04-25 M36 milestones doc sync

## 변경 파일
- `docs/MILESTONES.md`
- `work/4/25/2026-04-25-m36-milestones-doc-sync.md`

## 사용 skill
- `doc-sync`: M36 preference pause lifecycle 검증 완료 사실과 현재 milestone 문서의 drift를 맞추기 위해 사용했습니다.
- `work-log-closeout`: docs-only 변경 범위, 실행한 검증, 남은 리스크를 `/work` closeout으로 기록했습니다.

## 변경 이유
- `CONTROL_SEQ: 201` handoff에 따라 `docs/MILESTONES.md`가 M35까지만 기록하고 있던 상태를 M36 완료 상태로 갱신해야 했습니다.
- 기존 Next Priorities의 `M36 direction` 문구가 완료된 milestone을 다음 방향으로 남기고 있어 `M37 direction` 중심으로 교체해야 했습니다.

## 핵심 변경
- `Milestone 36: Preference Pause Lifecycle Verification` 섹션을 추가했습니다.
- M36 목표, guardrails, Axis 1/2 shipped infrastructure, closed 상태를 기록했습니다.
- Axis 1은 pause 후 두 번째 chat의 badge count N-1 확인으로 기록했습니다.
- Axis 2는 `page.reload()` 후 세 번째 chat의 count N-1 유지 확인과 PR #34 merge 완료로 기록했습니다.
- `Next 3 Implementation Priorities`를 M37 direction, `watcher_core` re-export note, E2E 환경 개선 note로 갱신했습니다.
- handoff 금지 범위에 따라 코드, 테스트, 다른 docs 파일은 수정하지 않았습니다.

## 검증
- `git diff --check -- docs/MILESTONES.md`
  - 통과, 출력 없음.
- `python3 -m unittest tests.test_docs_sync -v 2>&1 | tail -5`
  - 통과.
  - `Ran 13 tests in 0.077s`
  - `OK`
- `grep -n "Milestone 36\\|M37 direction" docs/MILESTONES.md | tail -5`
  - M36 섹션과 `M37 direction` 항목 확인.

## 남은 리스크
- 이번 handoff 범위는 `docs/MILESTONES.md` 단일 문서 동기화였습니다. 다른 product docs는 별도 doc-sync handoff가 있을 때 검토해야 합니다.
- 작업 전부터 있던 `verify/4/25/2026-04-25-m36-preference-pause-functional-e2e.md` 변경은 이번 implement handoff 범위 밖이라 건드리지 않았습니다.
- commit, 전체 gate, 다음 slice 선택은 수행하지 않았습니다.
