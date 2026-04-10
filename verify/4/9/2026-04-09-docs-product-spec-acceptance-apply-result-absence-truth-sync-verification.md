# docs: PRODUCT_SPEC ACCEPTANCE_CRITERIA reviewed-memory apply-result absence truth sync verification

## 변경 파일
- `verify/4/9/2026-04-09-docs-product-spec-acceptance-apply-result-absence-truth-sync-verification.md`
- `.pipeline/claude_handoff.md`

## 사용 skill
- `round-handoff`

## 변경 이유
- 최신 `/work`의 docs-only apply-result absence wording sync가 실제 `docs/PRODUCT_SPEC.md`, `docs/ACCEPTANCE_CRITERIA.md`, 그리고 현재 shipped apply/apply-result lifecycle truth와 맞는지 다시 확인해야 했습니다.
- 같은 날 reviewed-memory docs-only truth-sync가 이미 반복됐으므로, 다음 슬라이스는 또 하나의 한 줄 수정이 아니라 같은 family의 남은 root-doc bundle이어야 했습니다.

## 핵심 변경
- 최신 `/work`의 직접 수정 10곳은 truthful합니다.
  - `docs/PRODUCT_SPEC.md:1451`
  - `docs/PRODUCT_SPEC.md:1469`
  - `docs/ACCEPTANCE_CRITERIA.md:701`
  - `docs/ACCEPTANCE_CRITERIA.md:708`
  - `docs/ACCEPTANCE_CRITERIA.md:717`
  - `docs/ACCEPTANCE_CRITERIA.md:728`
  - `docs/ACCEPTANCE_CRITERIA.md:743`
  - `docs/ACCEPTANCE_CRITERIA.md:776`
  - `docs/ACCEPTANCE_CRITERIA.md:783`
  - `docs/ACCEPTANCE_CRITERIA.md:793`
- 최신 `/work`가 겨냥한 stale phrase는 현재 대상 문서에서 0건입니다.
  - `rg -n 'no reviewed-memory apply result|no apply result' docs/PRODUCT_SPEC.md docs/ACCEPTANCE_CRITERIA.md` → 0건
- current shipped apply/apply-result lifecycle와도 맞습니다.
  - `app/handlers/aggregate.py:393`
  - `app/handlers/aggregate.py:469`
  - `app/handlers/aggregate.py:531`
  - `docs/PRODUCT_SPEC.md:1537`
  - `docs/ACCEPTANCE_CRITERIA.md:923`
  - `docs/ACCEPTANCE_CRITERIA.md:930`
- 다만 같은 reviewed-memory apply-result absence family는 root docs 기준으로 아직 fully closed가 아닙니다.
  - `docs/TASK_BACKLOG.md:347`
  - `docs/NEXT_STEPS.md:399`
- 위 두 줄은 여전히 `no apply result`로 적혀 있어, 이미 shipped된 reviewed-memory apply result를 부재처럼 프레이밍합니다.

## 검증
- `sed -n '1,260p' AGENTS.md`
- `sed -n '1,260p' work/README.md`
- `sed -n '1,260p' verify/README.md`
- `sed -n '1,260p' .pipeline/README.md`
- `sed -n '1,260p' work/4/9/2026-04-09-docs-product-spec-acceptance-apply-result-absence-truth-sync.md`
- `sed -n '1,260p' verify/4/9/2026-04-09-docs-product-spec-acceptance-next-steps-promotion-gating-truth-sync-verification.md`
- `ls -1t work/4/9/*.md | head -n 12`
- `ls -1t verify/4/9/*.md | head -n 12`
- `git diff --check`
- `git diff -- docs/PRODUCT_SPEC.md docs/ACCEPTANCE_CRITERIA.md`
- `nl -ba docs/PRODUCT_SPEC.md | sed -n '1444,1472p;1528,1542p'`
- `nl -ba docs/ACCEPTANCE_CRITERIA.md | sed -n '696,796p;920,932p'`
- `nl -ba app/handlers/aggregate.py | sed -n '388,410p;464,476p;526,540p'`
- `rg -n 'no reviewed-memory apply result|no apply result' docs/PRODUCT_SPEC.md docs/ACCEPTANCE_CRITERIA.md`
- `rg -n 'reviewed-memory apply result is shipped separately above the capability path|apply result is shipped separately above the capability path|apply result is now also implemented|result_stage = result_recorded_effect_pending|effect_active' docs/PRODUCT_SPEC.md docs/ACCEPTANCE_CRITERIA.md docs/ARCHITECTURE.md docs/MILESTONES.md docs/NEXT_STEPS.md docs/TASK_BACKLOG.md app/handlers/aggregate.py`
- `rg -n 'no reviewed-memory apply result|no apply result|cross-session counting remains later than explicit local-store|cross-session counting remains later than local store|remains later because the repo still has no payload-visible reviewed-memory store|repeated-signal promotion is still premature because the repo still has no payload-visible reviewed-memory store' docs/PRODUCT_SPEC.md docs/ACCEPTANCE_CRITERIA.md docs/NEXT_STEPS.md docs/MILESTONES.md docs/ARCHITECTURE.md docs/TASK_BACKLOG.md`
- `nl -ba docs/TASK_BACKLOG.md | sed -n '340,350p'`
- `nl -ba docs/NEXT_STEPS.md | sed -n '392,402p'`
- Python unit test와 Playwright는 재실행하지 않았습니다. 최신 `/work`가 docs-only이고 code/test/runtime 변경을 주장하지 않았기 때문입니다.

## 남은 리스크
- 최신 `/work`의 `PRODUCT_SPEC` / `ACCEPTANCE_CRITERIA` sync 자체는 truthful합니다.
- 다만 같은 apply-result absence family의 residual(`docs/TASK_BACKLOG.md:347`, `docs/NEXT_STEPS.md:399`)이 남아 있으므로, 이번 라운드를 family 전체 closure로 보기는 어렵습니다.
