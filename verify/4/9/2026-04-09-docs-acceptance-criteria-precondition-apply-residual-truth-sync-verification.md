# docs: ACCEPTANCE_CRITERIA reviewed-memory precondition and apply residual truth sync verification

## 변경 파일
- `verify/4/9/2026-04-09-docs-acceptance-criteria-precondition-apply-residual-truth-sync-verification.md`
- `.pipeline/claude_handoff.md`

## 사용 skill
- `round-handoff`

## 변경 이유
- 최신 `/work`의 docs-only truth-sync가 실제 `docs/ACCEPTANCE_CRITERIA.md` 현재 상태와 shipped reviewed-memory precondition/apply truth에 맞는지 다시 확인해야 했습니다.
- 같은 reviewed-memory docs-only truth-sync family를 억지로 더 잘게 쪼개지 않으면서, 남은 residual을 한 번에 닫는 다음 Claude 슬라이스를 다시 좁혀야 했습니다.

## 핵심 변경
- 최신 `/work`의 직접 수정 3곳은 truthful합니다.
  - `docs/ACCEPTANCE_CRITERIA.md:845`
  - `docs/ACCEPTANCE_CRITERIA.md:970`
  - `docs/ACCEPTANCE_CRITERIA.md:976`
- stale phrase search 기준으로 이전 residual wording은 현재 0건입니다.
  - `no reviewed-memory apply, and no cross-session counting open in that slice`
  - `through later reviewed-memory-layer machinery`
  - `remain closed in that slice`
- 위 direct sync는 current shipped truth와 맞습니다.
  - `docs/TASK_BACKLOG.md:329`
  - `docs/TASK_BACKLOG.md:476`
  - `docs/NEXT_STEPS.md:532`
  - `docs/ARCHITECTURE.md:1138`
  - `docs/MILESTONES.md:199`
  - `docs/MILESTONES.md:278`
  - `docs/PRODUCT_SPEC.md:1473`
  - `docs/PRODUCT_SPEC.md:1498`
  - `docs/PRODUCT_SPEC.md:1537`
- 다만 최신 `/work`의 `남은 리스크 없음`은 과합니다.
  - 같은 capability-satisfaction wording family의 future-style residual이 root docs에 남아 있습니다.
  - `docs/PRODUCT_SPEC.md:1480`
  - `docs/PRODUCT_SPEC.md:1516`
  - `docs/ACCEPTANCE_CRITERIA.md:680`
- 위 residual은 current shipped same-session satisfaction / unblock truth가 이미 열렸는데도 full-family satisfaction 또는 same-session unblock을 future-only처럼 읽히게 만듭니다.
- 다음 슬라이스는 `docs/PRODUCT_SPEC.md`와 `docs/ACCEPTANCE_CRITERIA.md`의 remaining capability-satisfaction later-wording bundle로 고정했습니다.

## 검증
- `sed -n '1,240p' work/4/9/2026-04-09-docs-acceptance-criteria-precondition-apply-residual-truth-sync.md`
- `sed -n '1,240p' verify/4/9/2026-04-09-docs-next-steps-architecture-reviewed-memory-shipped-layer-truth-sync-verification.md`
- `sed -n '1,280p' .pipeline/claude_handoff.md`
- `ls -1t work/4/9/*.md | head -n 10`
- `ls -1t verify/4/9/*.md | head -n 10`
- `git diff --check`
- `git diff -- docs/ACCEPTANCE_CRITERIA.md`
- `rg -n 'no reviewed-memory apply, and no cross-session counting open in that slice|through later reviewed-memory-layer machinery|remain closed in that slice' docs/ACCEPTANCE_CRITERIA.md docs/PRODUCT_SPEC.md docs/ARCHITECTURE.md docs/MILESTONES.md docs/TASK_BACKLOG.md docs/NEXT_STEPS.md`
- `rg -n 'unblock later|satisfying the full family later|through later|remain contract exists only until later machinery can satisfy them|must remain closed until every reviewed-memory precondition is explicit|later same-session unblock|later machinery can satisfy' docs/ACCEPTANCE_CRITERIA.md docs/PRODUCT_SPEC.md docs/ARCHITECTURE.md docs/MILESTONES.md docs/TASK_BACKLOG.md docs/NEXT_STEPS.md`
- `nl -ba docs/ACCEPTANCE_CRITERIA.md | sed -n '838,846p;968,982p'`
- `nl -ba docs/ACCEPTANCE_CRITERIA.md | sed -n '580,690p'`
- `nl -ba docs/ACCEPTANCE_CRITERIA.md | sed -n '918,980p'`
- `nl -ba docs/PRODUCT_SPEC.md | sed -n '1440,1544p'`
- `nl -ba docs/PRODUCT_SPEC.md | sed -n '1474,1518p'`
- `nl -ba docs/ARCHITECTURE.md | sed -n '1118,1166p'`
- `nl -ba docs/MILESTONES.md | sed -n '278,340p'`
- `nl -ba docs/NEXT_STEPS.md | sed -n '384,420p'`
- Python unit test와 Playwright는 재실행하지 않았습니다. 최신 `/work`가 docs-only이고 code/test/runtime 변경을 주장하지 않았기 때문입니다.

## 남은 리스크
- 최신 `/work`의 direct `ACCEPTANCE_CRITERIA` sync 자체는 truthful합니다.
- 다만 같은 reviewed-memory capability-satisfaction wording family의 residual(`docs/PRODUCT_SPEC.md:1480`, `docs/PRODUCT_SPEC.md:1516`, `docs/ACCEPTANCE_CRITERIA.md:680`)이 남아 있으므로, 이번 라운드를 family 전체 closure로 보기는 어렵습니다.
