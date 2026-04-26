# 2026-04-26 M44 closure doc bundle

## 변경 파일
- `docs/MILESTONES.md`
- `docs/PRODUCT_SPEC.md`
- `docs/ACCEPTANCE_CRITERIA.md`

## 사용 skill
- `doc-sync`: M44 Axis 1 구현 사실을 현재 제품 문서와 acceptance 문서에 반영할 범위를 확인했다.
- `work-log-closeout`: 변경 파일, 실제 검증, 남은 리스크를 한국어 closeout으로 정리했다.

## 변경 이유
- M44 Axis 1에서 applied preferences popover가 status 배지와 마지막 전환 이유를 표시하도록 구현됐지만, 이전 closeout에서는 문서 변경이 금지되어 있었다.
- 이번 handoff는 코드와 테스트 변경 없이 `docs/MILESTONES.md`, `docs/PRODUCT_SPEC.md`, `docs/ACCEPTANCE_CRITERIA.md` 세 파일만 동기화해 M44를 닫도록 요구했다.

## 핵심 변경
- `docs/MILESTONES.md`에 `Milestone 44: Applied Preference Transparency` 섹션을 추가했다.
- `docs/MILESTONES.md`의 `Next 3 Implementation Priorities` 항목 2를 `M44 완료`로 갱신하고 M45 방향은 다음 advisory에서 확정한다고 표시했다.
- `docs/PRODUCT_SPEC.md`의 applied-preferences badge 설명 두 곳에, 배지 클릭 시 popover가 현재 상태(active 제외)와 `last_transition_reason`을 표시한다는 내용을 추가했다.
- `docs/ACCEPTANCE_CRITERIA.md`의 recent results acceptance 항목 아래에 applied preferences popover의 status 배지와 `이유: ...` 문구 표시 기준을 추가했다.
- 코드, 테스트, README, `docs/ARCHITECTURE.md`, `.pipeline/*` 파일은 변경하지 않았다.

## 검증
- `git diff --check -- docs/MILESTONES.md docs/PRODUCT_SPEC.md docs/ACCEPTANCE_CRITERIA.md` 통과, 출력 없음.
- `grep "Milestone 44" docs/MILESTONES.md` 통과: `### Milestone 44: Applied Preference Transparency`.
- `grep "M44 완료" docs/MILESTONES.md` 통과: `2. **M44 완료**: M44 Axis 1 (applied preference transparency — popover status 배지 + 전환 이유 표시) shipped. M45 방향은 다음 advisory에서 확정.`
- `python3 -m py_compile app/handlers/preferences.py` 통과, 출력 없음.
- `git diff --check -- docs/MILESTONES.md docs/PRODUCT_SPEC.md docs/ACCEPTANCE_CRITERIA.md work/4/26/2026-04-26-m44-closure-doc-bundle.md` 통과, 출력 없음.

## 남은 리스크
- 이번 라운드는 docs-only handoff라서 browser/Playwright, frontend TypeScript, 전체 unit suite는 실행하지 않았다.
- `README.md`, `docs/ARCHITECTURE.md`는 handoff 범위 밖이라 변경하지 않았다.
- 기존 작업트리의 untracked `report/gemini/**`, `verify/4/26/2026-04-26-b1-release-gate-pr35-reconcile.md`, `verify/4/26/2026-04-26-m43-publish-pr37-merge.md`, `work/4/26/2026-04-26-m43-publish-pr37-merge.md`, `work/4/26/2026-04-26-pr36-release-gate-merge.md`는 이번 handoff 범위 밖이므로 수정하지 않았다.
- commit, push, branch/PR 생성, merge는 수행하지 않았다.
