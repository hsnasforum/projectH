# review-queue reject/defer architecture docs parity bundle

## 변경 파일

- `docs/ARCHITECTURE.md`

## 사용 skill

- 없음

## 변경 이유

이전 라운드(`work/4/16/2026-04-16-review-queue-reject-defer-root-roadmap-docs-parity.md`)에서 `docs/MILESTONES.md`와 `docs/TASK_BACKLOG.md`의 reject/defer stale wording을 닫았고, verify에서 `docs/PRODUCT_SPEC.md`, `docs/ACCEPTANCE_CRITERIA.md`, `docs/NEXT_STEPS.md`는 이미 정합 상태임을 확인했습니다. 남은 동일 계열 drift가 `docs/ARCHITECTURE.md` (lines 1223–1229)에만 있어 이번 라운드에서 마지막 root-doc 정합을 닫습니다.

## 핵심 변경

1. **queue removal wording** (line 1223): `accept`-only → `accept`, `reject`, or `defer` 세 action 모두로 pending item 제거.
2. **later vocabulary** (line 1226): `edit`, `reject`, and `defer` are still deferred → `edit` is still deferred. reject/defer는 이미 shipped.
3. **API truth** (line 1229): `one \`accept\` review action API but still has no \`edit\` / \`reject\` / \`defer\` API` → `\`accept\`, \`reject\`, and \`defer\` review action APIs but still has no \`edit\` API`.

## 검증

- `nl -ba docs/ARCHITECTURE.md | sed -n '1218,1232p'` → 세 줄 모두 shipped 상태 반영 확인
- `rg -n 'accept-only|one \x60accept\x60 action|no \x60edit\x60 / \x60reject\x60 / \x60defer\x60 API|\x60edit\x60, \x60reject\x60, and \x60defer\x60 are still deferred' docs/ARCHITECTURE.md docs/PRODUCT_SPEC.md docs/NEXT_STEPS.md docs/ACCEPTANCE_CRITERIA.md` → no matches (stale pattern 소멸)
- `git diff --check -- docs/ARCHITECTURE.md work/4/16` → clean

## 남은 리스크

- review-action 계열 root-doc drift는 이 라운드로 전부 닫힘. `docs/ARCHITECTURE.md`의 다른 section에서 review-action과 무관한 별도 stale wording이 있을 수 있으나, 이번 handoff scope 밖.
