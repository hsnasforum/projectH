# 2026-04-25 M34-M35 milestones doc sync

## 변경 파일
- `docs/MILESTONES.md`
- `work/4/25/2026-04-25-m34-m35-milestones-doc-sync.md`

## 사용 skill
- `doc-sync`: M34/M35 구현·검증 결과와 현재 milestone 문서의 drift를 맞추기 위해 사용했습니다.
- `work-log-closeout`: docs-only 변경 범위, 실행한 검증, 남은 리스크를 `/work` closeout으로 기록했습니다.

## 변경 이유
- `CONTROL_SEQ: 188` handoff에 따라 `docs/MILESTONES.md`가 M33까지만 기록하고 있던 상태를 M34/M35 완료 상태로 갱신해야 했습니다.
- 기존 Next Priorities의 `PR #33 merge`, `M34 direction` 문구가 현재 상태와 맞지 않아 새 PR/M36 방향 문구로 교체해야 했습니다.

## 핵심 변경
- `Milestone 34: Applied Preference Loop Visibility` 섹션을 추가했습니다.
- `Milestone 35: Interactive Applied Preference Management` 섹션을 추가했습니다.
- M34/M35 각 섹션에 목표, guardrails, shipped infrastructure, closed 상태를 기록했습니다.
- `Next 3 Implementation Priorities`를 새 PR 생성 대기, M36 direction, `watcher_core` re-export note로 갱신했습니다.
- handoff 금지 범위에 따라 `README.md`, `PRODUCT_SPEC.md`, 코드, 테스트 파일은 수정하지 않았습니다.

## 검증
- `git diff --check -- docs/MILESTONES.md`
  - 통과, 출력 없음.
- `python3 -m unittest tests.test_docs_sync -v 2>&1 | tail -5`
  - 통과.
  - `Ran 13 tests in 0.026s`
  - `OK`
- `grep -n "Milestone 34\\|Milestone 35\\|New PR\\|M36 direction" docs/MILESTONES.md | tail -10`
  - M34/M35 섹션과 `New PR`, `M36 direction` 항목 확인.

## 남은 리스크
- 이번 handoff 범위는 `docs/MILESTONES.md` 단일 문서 동기화였습니다. README, product spec, acceptance docs는 별도 doc-sync handoff가 있을 때 검토해야 합니다.
- commit, 전체 gate, 다음 slice 선택은 수행하지 않았습니다.
