# docs: PRODUCT_SPEC ACCEPTANCE_CRITERIA NEXT_STEPS promotion-gating truth sync verification

## 변경 파일
- `verify/4/9/2026-04-09-docs-product-spec-acceptance-next-steps-promotion-gating-truth-sync-verification.md`
- `.pipeline/claude_handoff.md`

## 사용 skill
- `round-handoff`

## 변경 이유
- 최신 `/work`의 docs-only promotion-gating 문구 수정 4곳이 현재 root docs와 구현 앵커에 맞는지 다시 확인해야 했습니다.
- 같은 날 reviewed-memory docs-only truth-sync가 이미 반복됐으므로, 다음 슬라이스는 또 하나의 한 줄 수정이 아니라 실제 현재 구현과 어긋나는 남은 root-doc bundle이어야 했습니다.

## 핵심 변경
- 최신 `/work`의 직접 수정 4곳은 truthful합니다.
  - `docs/PRODUCT_SPEC.md:1474`
  - `docs/ACCEPTANCE_CRITERIA.md:580`
  - `docs/ACCEPTANCE_CRITERIA.md:641`
  - `docs/NEXT_STEPS.md:108`
- targeted stale phrase search 기준으로 이번 `/work`가 겨냥한 promotion-gating 문구는 현재 0건입니다.
- current shipped capability truth도 문서와 맞습니다.
  - `app/serializers.py:1471`의 `reviewed_memory_unblock_contract.unblock_status`는 계속 `blocked_all_required`입니다.
  - `app/serializers.py:1515`의 `reviewed_memory_capability_status.capability_outcome`는 matching `reviewed_memory_capability_basis`가 있을 때 `unblocked_all_required`로 열립니다.
- 다만 다음 reviewed-memory docs bundle은 아직 남아 있습니다.
  - `docs/PRODUCT_SPEC.md:1451`
  - `docs/PRODUCT_SPEC.md:1469`
  - `docs/ACCEPTANCE_CRITERIA.md:708`
  - `docs/ACCEPTANCE_CRITERIA.md:717`
  - `docs/ACCEPTANCE_CRITERIA.md:728`
  - `docs/ACCEPTANCE_CRITERIA.md:743`
  - `docs/ACCEPTANCE_CRITERIA.md:776`
  - `docs/ACCEPTANCE_CRITERIA.md:783`
  - `docs/ACCEPTANCE_CRITERIA.md:793`
- 위 잔여 문구는 shipped `reviewed-memory apply result`를 여전히 "없음"으로 적습니다.
  - 반면 current shipped truth는 이미 apply/apply-result/stop-apply/reversal/conflict-visibility까지 열려 있습니다.
  - `docs/PRODUCT_SPEC.md:1537`
  - `docs/ACCEPTANCE_CRITERIA.md:923`
  - `docs/ACCEPTANCE_CRITERIA.md:930`
  - `docs/ARCHITECTURE.md:1164`
  - `docs/TASK_BACKLOG.md:717`
  - `app/handlers/aggregate.py:393`
  - `app/handlers/aggregate.py:469`
  - `app/handlers/aggregate.py:531`

## 검증
- `sed -n '1,260p' AGENTS.md`
- `sed -n '1,260p' work/README.md`
- `sed -n '1,260p' verify/README.md`
- `sed -n '1,260p' .pipeline/README.md`
- `sed -n '1,260p' work/4/9/2026-04-09-docs-product-spec-acceptance-next-steps-promotion-gating-truth-sync.md`
- `sed -n '1,260p' verify/4/9/2026-04-09-docs-product-spec-acceptance-capability-satisfaction-later-wording-truth-sync-verification.md`
- `git diff --check`
- `git diff -- docs/PRODUCT_SPEC.md docs/ACCEPTANCE_CRITERIA.md docs/NEXT_STEPS.md`
- `nl -ba docs/PRODUCT_SPEC.md | sed -n '1466,1484p;1490,1504p;1510,1522p'`
- `nl -ba docs/ACCEPTANCE_CRITERIA.md | sed -n '572,586p;636,648p;674,684p;964,974p'`
- `nl -ba docs/NEXT_STEPS.md | sed -n '100,112p;206,214p'`
- `nl -ba docs/MILESTONES.md | sed -n '190,202p;274,282p'`
- `rg -n 'promotion-ineligible until|remain out of scope until a later local store, rollback, conflict, and reviewed-memory boundary exists|must remain closed until every reviewed-memory precondition is explicit|full reviewed-memory precondition family exists and is satisfied|until precondition family is satisfied in full' docs`
- `rg -n 'reviewed_memory_capability_status|unblocked_all_required|reviewed_memory_unblock_contract|aggregate_promotion_marker|reviewed_memory_precondition_status|reviewed_memory_planning_target_ref' -g '!work/**' -g '!verify/**'`
- `nl -ba app/serializers.py | sed -n '1428,1524p'`
- `nl -ba app/serializers.py | sed -n '3770,3904p'`
- `nl -ba docs/PRODUCT_SPEC.md | sed -n '1444,1472p'`
- `nl -ba docs/ACCEPTANCE_CRITERIA.md | sed -n '700,796p'`
- `rg -n 'no reviewed-memory apply result' docs/PRODUCT_SPEC.md docs/ACCEPTANCE_CRITERIA.md docs/NEXT_STEPS.md docs/MILESTONES.md docs/ARCHITECTURE.md docs/TASK_BACKLOG.md`
- `rg -n 'apply result is now also implemented|reviewed-memory apply result is shipped|the apply result is now also implemented|result_stage = result_recorded_effect_pending|effect_active' docs/PRODUCT_SPEC.md docs/ACCEPTANCE_CRITERIA.md docs/NEXT_STEPS.md docs/MILESTONES.md docs/ARCHITECTURE.md docs/TASK_BACKLOG.md app/handlers/aggregate.py`
- Python unit test와 Playwright는 재실행하지 않았습니다. 최신 `/work`가 docs-only이고 code/test/runtime 변경을 주장하지 않았기 때문입니다.

## 남은 리스크
- 최신 `/work`의 promotion-gating sync 자체는 truthful합니다.
- 다만 root docs의 `reviewed-memory apply result 없음` 잔여 문구가 현재 shipped apply/apply-result lifecycle과 충돌하므로, 다음 슬라이스는 `docs/PRODUCT_SPEC.md`와 `docs/ACCEPTANCE_CRITERIA.md`의 해당 잔여 묶음을 한 번에 닫아야 합니다.
