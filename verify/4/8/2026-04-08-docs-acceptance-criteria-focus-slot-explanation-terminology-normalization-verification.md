## 변경 파일
- `verify/4/8/2026-04-08-docs-acceptance-criteria-focus-slot-explanation-terminology-normalization-verification.md`
- `.pipeline/claude_handoff.md`

## 사용 skill
- `round-handoff`

## 변경 이유
- latest `/work` `work/4/8/2026-04-08-docs-acceptance-criteria-focus-slot-explanation-terminology-normalization.md`가 실제 문서 상태와 맞는지 다시 확인하고, same-family focus-slot explanation terminology normalization이 정말로 current docs hierarchy에서 닫혔는지 검증해야 했습니다.
- same-day latest `/verify`와 기존 `.pipeline/claude_handoff.md`는 `docs/ACCEPTANCE_CRITERIA.md` 한 줄 terminology drift를 다음 exact slice로 고정한 상태였으므로, 이번 `/work`가 그 잔여 리스크를 truthfully 닫았는지 재판정한 뒤 persistent verification과 next handoff를 갱신할 필요가 있었습니다.

## 핵심 변경
- latest `/work`는 truthful했습니다.
  - [`docs/ACCEPTANCE_CRITERIA.md:41`](/home/xpdlqj/code/projectH/docs/ACCEPTANCE_CRITERIA.md#L41)은 실제로 `is still single-source`로 바뀌어 있었고, `git diff -- docs/ACCEPTANCE_CRITERIA.md`는 clean이었습니다.
  - `rg -n "remains single-source|stayed single-source|improved / regressed / unchanged|improved, regressed, stayed single-source|remains unresolved" README.md docs plandoc -S` 결과도 root `README.md` / `docs/` 범위에서는 old wording 잔여를 찾지 못했습니다.
  - `git diff --check`도 clean이었습니다.
- `/work`의 “3개 핵심 문서 전체 4-state 용어 일관성 확인”, “전체 문서 계층에서 완료됨” 결론도 이번에는 과장으로 보이지 않았습니다.
  - [`README.md:69`](/home/xpdlqj/code/projectH/README.md#L69), [`README.md:127`](/home/xpdlqj/code/projectH/README.md#L127), [`docs/PRODUCT_SPEC.md:106`](/home/xpdlqj/code/projectH/docs/PRODUCT_SPEC.md#L106), [`docs/PRODUCT_SPEC.md:291`](/home/xpdlqj/code/projectH/docs/PRODUCT_SPEC.md#L291), [`docs/PRODUCT_SPEC.md:310`](/home/xpdlqj/code/projectH/docs/PRODUCT_SPEC.md#L310), [`docs/ACCEPTANCE_CRITERIA.md:41`](/home/xpdlqj/code/projectH/docs/ACCEPTANCE_CRITERIA.md#L41), [`docs/ACCEPTANCE_CRITERIA.md:1337`](/home/xpdlqj/code/projectH/docs/ACCEPTANCE_CRITERIA.md#L1337), [`docs/NEXT_STEPS.md:15`](/home/xpdlqj/code/projectH/docs/NEXT_STEPS.md#L15), [`docs/TASK_BACKLOG.md:24`](/home/xpdlqj/code/projectH/docs/TASK_BACKLOG.md#L24), [`docs/MILESTONES.md:37`](/home/xpdlqj/code/projectH/docs/MILESTONES.md#L37), [`docs/project-brief.md:81`](/home/xpdlqj/code/projectH/docs/project-brief.md#L81), [`docs/PRODUCT_PROPOSAL.md:61`](/home/xpdlqj/code/projectH/docs/PRODUCT_PROPOSAL.md#L61)이 모두 `reinforced / regressed / still single-source / still unresolved` family를 사용하고 있습니다.
- 다음 exact slice는 `Docs PRODUCT_SPEC ARCHITECTURE claim_coverage_progress_summary field-shape truth sync`로 고정했습니다.
  - current implementation/tests는 이미 `previous_status`, `previous_status_label`, `progress_state`, `is_focus_slot`까지 serialize하고 있습니다. 예를 들어 [`core/agent_loop.py:4203`](/home/xpdlqj/code/projectH/core/agent_loop.py#L4203), [`core/agent_loop.py:4205`](/home/xpdlqj/code/projectH/core/agent_loop.py#L4205), [`core/agent_loop.py:4207`](/home/xpdlqj/code/projectH/core/agent_loop.py#L4207), [`app/serializers.py:950`](/home/xpdlqj/code/projectH/app/serializers.py#L950), [`app/serializers.py:952`](/home/xpdlqj/code/projectH/app/serializers.py#L952), [`app/serializers.py:954`](/home/xpdlqj/code/projectH/app/serializers.py#L954), [`tests/test_web_app.py:5435`](/home/xpdlqj/code/projectH/tests/test_web_app.py#L5435), [`tests/test_web_app.py:5437`](/home/xpdlqj/code/projectH/tests/test_web_app.py#L5437)이 그 shape를 확인합니다.
  - 반면 현재 문서는 [`docs/PRODUCT_SPEC.md:257`](/home/xpdlqj/code/projectH/docs/PRODUCT_SPEC.md#L257), [`docs/ARCHITECTURE.md:171`](/home/xpdlqj/code/projectH/docs/ARCHITECTURE.md#L171)에서 `claim_coverage_progress_summary` 이름만 열거하고 있어 stored/session metadata current shape가 문서상으로는 충분히 드러나지 않습니다.
  - 같은 family의 다음 current-risk는 user-visible wording이 아니라 metadata/schema truth 누락이므로, `PRODUCT_SPEC`와 `ARCHITECTURE`를 한 번에 맞추는 bounded docs slice가 가장 직접적입니다.
- `.pipeline/claude_handoff.md`도 위 판단에 맞춰 새 next slice 기준으로 갱신했습니다.

## 검증
- `sed -n '1,260p' work/4/8/2026-04-08-docs-acceptance-criteria-focus-slot-explanation-terminology-normalization.md`
- `sed -n '1,260p' verify/4/8/2026-04-08-docs-product-spec-focus-slot-explanation-terminology-normalization-verification.md`
- `sed -n '1,260p' .pipeline/claude_handoff.md`
- `git status --short`
- `nl -ba docs/ACCEPTANCE_CRITERIA.md | sed -n '39,42p'`
- `git diff -- docs/ACCEPTANCE_CRITERIA.md`
- `rg -n "remains single-source|is still single-source|still single-source|remains unresolved|is still unresolved|still unresolved|improved, regressed, stayed single-source|reinforced / regressed / still single-source / still unresolved" README.md docs/PRODUCT_SPEC.md docs/ACCEPTANCE_CRITERIA.md docs/MILESTONES.md docs/TASK_BACKLOG.md docs/NEXT_STEPS.md docs/project-brief.md docs/PRODUCT_PROPOSAL.md -S`
- `git diff --check`
- `rg -n "remains single-source|stayed single-source|improved / regressed / unchanged|improved, regressed, stayed single-source|remains unresolved" README.md docs plandoc -S`
- `rg -n "focus-slot reinvestigation explanation|focus-slot explanation|claim coverage panel" docs/ARCHITECTURE.md docs README.md plandoc -S`
- `rg -n "claim_coverage|claim coverage|focus-slot|is_focus_slot|verification-strength|source-role trust" docs/ARCHITECTURE.md docs/PRODUCT_SPEC.md docs/ACCEPTANCE_CRITERIA.md README.md -S`
- `nl -ba docs/PRODUCT_SPEC.md | sed -n '148,156p'`
- `nl -ba docs/ARCHITECTURE.md | sed -n '120,136p'`
- `nl -ba docs/ARCHITECTURE.md | sed -n '160,180p'`
- `nl -ba docs/ARCHITECTURE.md | sed -n '1286,1304p'`
- `nl -ba docs/PRODUCT_SPEC.md | sed -n '248,266p'`
- `rg -n "claim_coverage_progress_summary|progress_state|is_focus_slot|previous_status|current_status" core app tests storage -S`
- `rg -n "claim_coverage_progress_summary|progress_state|is_focus_slot|previous_status|current_status" docs README.md -S`

## 남은 리스크
- user-facing focus-slot explanation terminology drift는 root docs/README 범위에서 닫혔지만, [`docs/PRODUCT_SPEC.md:257`](/home/xpdlqj/code/projectH/docs/PRODUCT_SPEC.md#L257)와 [`docs/ARCHITECTURE.md:171`](/home/xpdlqj/code/projectH/docs/ARCHITECTURE.md#L171)은 아직 `claim_coverage_progress_summary`와 `claim_coverage`의 concrete field shape를 설명하지 않아 metadata/schema truth가 문서에 충분히 드러나지 않습니다.
- `plandoc/`의 `remains unresolved` hit들은 claim-coverage wording family가 아니라 reviewed-memory draft 문맥이어서 이번 범위에서는 수정하지 않았습니다.
- unrelated dirty worktree(`.gitignore`, `.pipeline/README.md`, `AGENTS.md`, `CLAUDE.md`, `GEMINI.md`, `PROJECT_CUSTOM_INSTRUCTIONS.md`, `pipeline_gui/*`, `watcher_core.py`, 관련 tests, `work/README.md`, `verify/README.md`, `report/gemini/README.md`, 기타 unrelated `work/` / `verify/` note)는 이번 검증 범위 밖이라 손대지 않았습니다.
