# docs: PRODUCT_SPEC and ACCEPTANCE_CRITERIA capability-satisfaction later-wording truth sync verification

## 변경 파일
- `verify/4/9/2026-04-09-docs-product-spec-acceptance-capability-satisfaction-later-wording-truth-sync-verification.md`
- `.pipeline/claude_handoff.md`

## 사용 skill
- `round-handoff`

## 변경 이유
- 최신 `/work`의 docs-only truth-sync가 실제 `docs/PRODUCT_SPEC.md`, `docs/ACCEPTANCE_CRITERIA.md`, 그리고 current shipped reviewed-memory capability truth와 맞는지 다시 확인해야 했습니다.
- 같은 reviewed-memory docs-only truth-sync family를 또 하나의 micro-slice로 쪼개지 않으면서, 남은 promotion-gating / unblock-intro residual을 한 번에 닫는 다음 Claude 슬라이스를 다시 좁혀야 했습니다.

## 핵심 변경
- 최신 `/work`의 직접 수정 3곳은 truthful합니다.
  - `docs/PRODUCT_SPEC.md:1480`
  - `docs/PRODUCT_SPEC.md:1516`
  - `docs/ACCEPTANCE_CRITERIA.md:680`
- stale phrase search 기준으로 이전 residual wording은 현재 0건입니다.
  - `satisfying the full family later`
  - `same-session unblock later`
  - `later machinery can satisfy`
- 위 direct sync는 current shipped truth와 맞습니다.
  - `docs/PRODUCT_SPEC.md:1473`
  - `docs/PRODUCT_SPEC.md:1498`
  - `docs/PRODUCT_SPEC.md:1537`
  - `docs/ACCEPTANCE_CRITERIA.md:970`
  - `docs/MILESTONES.md:199`
  - `docs/MILESTONES.md:278`
  - `docs/MILESTONES.md:281`
  - `docs/NEXT_STEPS.md:212`
- 다만 최신 `/work`의 `남은 리스크 없음`은 과합니다.
  - 같은 promotion-gating / unblock-intro wording family의 residual이 root docs에 남아 있습니다.
  - `docs/PRODUCT_SPEC.md:1474`
  - `docs/ACCEPTANCE_CRITERIA.md:580`
  - `docs/ACCEPTANCE_CRITERIA.md:641`
  - `docs/NEXT_STEPS.md:108`
- 위 residual은 promotion-ineligible 또는 unblock gating을 current shipped capability satisfaction과 잘못 연결합니다.
  - current `reviewed_memory_capability_status.capability_outcome = unblocked_all_required`는 이미 shipped입니다.
  - reviewed-memory apply path도 이미 precondition family above layer로 shipped입니다.
  - repeated-signal promotion과 cross-session counting만 later입니다.
- 다음 슬라이스는 `docs/PRODUCT_SPEC.md`, `docs/ACCEPTANCE_CRITERIA.md`, `docs/NEXT_STEPS.md`의 remaining promotion-gating / unblock-intro wording bundle로 고정했습니다.

## 검증
- `sed -n '1,240p' work/4/9/2026-04-09-docs-product-spec-acceptance-capability-satisfaction-later-wording-truth-sync.md`
- `sed -n '1,240p' verify/4/9/2026-04-09-docs-acceptance-criteria-precondition-apply-residual-truth-sync-verification.md`
- `sed -n '1,320p' .pipeline/claude_handoff.md`
- `ls -1t work/4/9/*.md | head -n 12`
- `ls -1t verify/4/9/*.md | head -n 12`
- `git diff --check`
- `git diff -- docs/PRODUCT_SPEC.md docs/ACCEPTANCE_CRITERIA.md`
- `rg -n 'satisfying the full family later|later same-session unblock|same-session unblock is shipped and must remain separate|contract exists as read-only surfaces|source-family-plus-basis path above them|source-family-plus-basis chain' docs/PRODUCT_SPEC.md docs/ACCEPTANCE_CRITERIA.md docs/MILESTONES.md docs/NEXT_STEPS.md docs/ARCHITECTURE.md docs/TASK_BACKLOG.md`
- `rg -n 'promotion-ineligible until|remain out of scope until a later local store, rollback, conflict, and reviewed-memory boundary exists|must remain closed until every reviewed-memory precondition is explicit' docs/PRODUCT_SPEC.md docs/ACCEPTANCE_CRITERIA.md docs/MILESTONES.md docs/NEXT_STEPS.md docs/ARCHITECTURE.md docs/TASK_BACKLOG.md`
- `rg -n 'promotion and cross-session counting remain later|current shipped `reviewed_memory_capability_status.capability_outcome = unblocked_all_required`|the reviewed-memory apply path is now shipped above this precondition family|same-session aggregates stay promotion-ineligible' docs/MILESTONES.md docs/NEXT_STEPS.md docs/PRODUCT_SPEC.md docs/ACCEPTANCE_CRITERIA.md docs/TASK_BACKLOG.md`
- `nl -ba docs/PRODUCT_SPEC.md | sed -n '1474,1518p'`
- `nl -ba docs/PRODUCT_SPEC.md | sed -n '1468,1476p'`
- `nl -ba docs/ACCEPTANCE_CRITERIA.md | sed -n '674,684p'`
- `nl -ba docs/ACCEPTANCE_CRITERIA.md | sed -n '576,586p;639,684p'`
- `nl -ba docs/NEXT_STEPS.md | sed -n '100,110p'`
- `nl -ba docs/MILESTONES.md | sed -n '190,200p;278,281p'`
- Python unit test와 Playwright는 재실행하지 않았습니다. 최신 `/work`가 docs-only이고 code/test/runtime 변경을 주장하지 않았기 때문입니다.

## 남은 리스크
- 최신 `/work`의 direct `PRODUCT_SPEC` / `ACCEPTANCE_CRITERIA` sync 자체는 truthful합니다.
- 다만 같은 reviewed-memory promotion-gating / unblock-intro wording family의 residual(`docs/PRODUCT_SPEC.md:1474`, `docs/ACCEPTANCE_CRITERIA.md:580`, `docs/ACCEPTANCE_CRITERIA.md:641`, `docs/NEXT_STEPS.md:108`)이 남아 있으므로, 이번 라운드를 family 전체 closure로 보기는 어렵습니다.
