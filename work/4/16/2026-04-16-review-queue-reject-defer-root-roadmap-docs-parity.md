# review-queue reject/defer remaining root-roadmap docs parity bundle

## 변경 파일

- `docs/MILESTONES.md`
- `docs/TASK_BACKLOG.md`

## 사용 skill

- 없음

## 변경 이유

`reject` / `defer` review action의 browser contract는 이전 verify 라운드(`verify/4/15/2026-04-15-review-queue-reject-defer-quick-meta-browser-parity-verification.md`)에서 이미 truthfully 확인되었습니다. 코드와 browser assertion은 정합하지만 root roadmap 문서 두 곳에 accept-only 또는 reject/defer를 later로 분류하는 stale wording이 남아 있어 이번 라운드에서 닫습니다.

## 핵심 변경

1. **`docs/MILESTONES.md` Milestone 7 subsection** (line 406 부근): `accept`-only로 기술된 `candidate_review_record` 설명을 `accept`, `reject`, or `defer`로 수정. "still later" 목록에서 `reject`와 `defer`를 제거하고 `edit`만 later로 유지.
2. **`docs/MILESTONES.md` Next 3 Implementation Priorities** (line 454 부근): `Keep \`edit\` / \`reject\` / \`defer\``를 `Keep \`edit\``로 수정하고, reject/defer가 이미 shipped임을 괄호 주석으로 명시.
3. **`docs/TASK_BACKLOG.md` Next 3 Implementation Priorities** (line 165 부근): 동일한 stale wording을 동일하게 수정.

## 검증

- `rg -n -e 'accept.*reject.*defer' -e 'Keep \x60edit\x60 / \x60reject\x60 / \x60defer\x60' -e 'candidate_review_record.*through \x60accept\x60' docs/MILESTONES.md docs/TASK_BACKLOG.md` → stale pattern 없음 확인
- `git diff --check -- docs/MILESTONES.md docs/TASK_BACKLOG.md` → clean
- `docs/NEXT_STEPS.md`, `docs/PRODUCT_SPEC.md` reread → 이미 shipped 상태를 정확히 반영하므로 변경 불필요

## 남은 리스크

- `docs/ARCHITECTURE.md` (lines 1223–1229)에도 accept-only 및 reject/defer-as-later stale wording이 남아 있으나 이번 handoff scope 밖임.
