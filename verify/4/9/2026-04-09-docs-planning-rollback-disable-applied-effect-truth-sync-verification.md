# docs: NEXT_STEPS MILESTONES TASK_BACKLOG rollback-disable applied-effect wording truth sync verification

## 변경 파일
- `verify/4/9/2026-04-09-docs-planning-rollback-disable-applied-effect-truth-sync-verification.md`
- `.pipeline/claude_handoff.md`

## 사용 skill
- `round-handoff`

## 변경 이유
- 최신 `/work` note의 planning-doc rollback/disable wording 수정이 실제 문서 상태와 root authority truth에 맞는지 다시 확인해야 했습니다.
- 같은 reviewed-memory precondition planning family 안에서 다음 Claude 슬라이스를 한 개로 좁혀야 했습니다.

## 핵심 변경
- 최신 `/work`의 직접 수정 자체는 일부 truthful했습니다.
  - `docs/NEXT_STEPS.md:134`
  - `docs/NEXT_STEPS.md:135`
  - `docs/NEXT_STEPS.md:137`
  - `docs/NEXT_STEPS.md:138`
  - `docs/NEXT_STEPS.md:139`
  - `docs/NEXT_STEPS.md:141`
  - `docs/MILESTONES.md:214`
  - `docs/MILESTONES.md:226`
  - `docs/TASK_BACKLOG.md:319`
  - `docs/TASK_BACKLOG.md:320`
  - `docs/TASK_BACKLOG.md:351`
  - `docs/TASK_BACKLOG.md:381`
  는 current shipped applied-effect wording과 맞습니다.
- 다만 closeout의 `남은 리스크 없음`은 과합니다.
  - 같은 slice 안에 residual이 그대로 남아 있습니다.
  - `docs/MILESTONES.md:212`
  - `docs/MILESTONES.md:224`
  - `docs/TASK_BACKLOG.md:352`
  - `docs/TASK_BACKLOG.md:361`
  - `docs/TASK_BACKLOG.md:382`
  - `docs/TASK_BACKLOG.md:391`
  는 아직 `later applied reviewed-memory effect` 또는 `later applied reviewed-memory influence`를 유지합니다.
- 이 residual은 root authority docs와 current shipped semantics와 어긋납니다.
  - `docs/PRODUCT_SPEC.md:1137`
  - `docs/PRODUCT_SPEC.md:1142`
  - `docs/PRODUCT_SPEC.md:1145`
  - `docs/PRODUCT_SPEC.md:1148`
  - `docs/ARCHITECTURE.md:866`
  - `docs/ARCHITECTURE.md:869`
  - `docs/ARCHITECTURE.md:872`
  - `docs/ARCHITECTURE.md:875`
  - `docs/ACCEPTANCE_CRITERIA.md:649`
  - `docs/ACCEPTANCE_CRITERIA.md:652`
  - `docs/ACCEPTANCE_CRITERIA.md:655`
  - `docs/ACCEPTANCE_CRITERIA.md:657`
  - `app/handlers/aggregate.py:392`
  - `app/handlers/aggregate.py:467`
  - `app/handlers/aggregate.py:529`
  - `tests/test_web_app.py:7488`
  - `tests/test_web_app.py:7643`
- 다음 Claude 슬라이스는 `MILESTONES`와 `TASK_BACKLOG`의 remaining later-applied target/influence wording sync로 고정했습니다. 이미 닫힌 `NEXT_STEPS`까지 다시 건드리는 것보다, 남은 exact residual만 닫는 편이 더 좁고 truthful합니다.

## 검증
- `sed -n '1,260p' work/4/9/2026-04-09-docs-planning-rollback-disable-applied-effect-truth-sync.md`
- `sed -n '1,260p' verify/4/9/2026-04-09-docs-next-steps-operator-auditable-shipped-truth-sync-verification.md`
- `sed -n '1,320p' .pipeline/claude_handoff.md`
- `nl -ba docs/NEXT_STEPS.md | sed -n '132,141p'`
- `nl -ba docs/MILESTONES.md | sed -n '212,226p'`
- `nl -ba docs/TASK_BACKLOG.md | sed -n '318,320p'`
- `nl -ba docs/TASK_BACKLOG.md | sed -n '350,352p'`
- `nl -ba docs/TASK_BACKLOG.md | sed -n '358,361p'`
- `nl -ba docs/TASK_BACKLOG.md | sed -n '380,382p'`
- `nl -ba docs/TASK_BACKLOG.md | sed -n '388,391p'`
- `rg -n 'later reviewed-memory effect|later apply|later applied influence|later applied reviewed-memory effect|later applied' docs/NEXT_STEPS.md docs/MILESTONES.md docs/TASK_BACKLOG.md`
- `nl -ba docs/PRODUCT_SPEC.md | sed -n '1135,1148p'`
- `nl -ba docs/ARCHITECTURE.md | sed -n '864,875p'`
- `nl -ba docs/ACCEPTANCE_CRITERIA.md | sed -n '647,657p'`
- `nl -ba app/handlers/aggregate.py | sed -n '392,554p'`
- `nl -ba tests/test_web_app.py | sed -n '7484,7490p'`
- `nl -ba tests/test_web_app.py | sed -n '7641,7646p'`
- `git diff --check`
- Python unit test와 Playwright는 이번 검증 라운드에서 재실행하지 않았습니다.

## 남은 리스크
- planning docs의 rollback/disable summary family가 아직 `MILESTONES`와 `TASK_BACKLOG`에서 later-applied wording을 남겨, current shipped applied-effect semantics가 완전히 닫히지 않았습니다.
