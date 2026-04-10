## 변경 파일
- `verify/4/8/2026-04-08-docs-product-spec-architecture-claim-coverage-progress-summary-field-shape-truth-sync-verification.md`
- `.pipeline/claude_handoff.md`

## 사용 skill
- `round-handoff`

## 변경 이유
- latest `/work` `work/4/8/2026-04-08-docs-product-spec-architecture-claim-coverage-progress-summary-field-shape-truth-sync.md`가 실제 문서 상태와 맞는지 다시 확인하고, same-family claim-coverage metadata field-shape docs가 truthfully 닫혔는지 검증해야 했습니다.
- same-day latest `/verify`와 기존 `.pipeline/claude_handoff.md`는 `claim_coverage_progress_summary` / `claim_coverage` field-shape docs sync를 다음 exact slice로 고정한 상태였으므로, 이번 `/work`가 그 범위를 정확히 닫았는지 재판정한 뒤 persistent verification과 next handoff를 갱신할 필요가 있었습니다.

## 핵심 변경
- latest `/work`는 `docs/PRODUCT_SPEC.md` / `docs/ARCHITECTURE.md`의 field-shape 문서화와 rerun 자체는 맞았지만, 완전히 truthful하지는 않았습니다.
  - [`docs/PRODUCT_SPEC.md:256`](/home/xpdlqj/code/projectH/docs/PRODUCT_SPEC.md#L256)과 [`docs/PRODUCT_SPEC.md:257`](/home/xpdlqj/code/projectH/docs/PRODUCT_SPEC.md#L257), [`docs/ARCHITECTURE.md:170`](/home/xpdlqj/code/projectH/docs/ARCHITECTURE.md#L170)과 [`docs/ARCHITECTURE.md:171`](/home/xpdlqj/code/projectH/docs/ARCHITECTURE.md#L171)에 `claim_coverage` / `claim_coverage_progress_summary` shape 설명이 실제로 추가되어 있었습니다.
  - `git diff -- docs/PRODUCT_SPEC.md docs/ARCHITECTURE.md`는 clean이었고, `git diff --check`도 clean이었습니다.
  - `rg -n "claim_coverage_progress_summary|previous_status|previous_status_label|progress_state|progress_label|is_focus_slot|rendered_as|support_count|candidate_count|status_label" docs/PRODUCT_SPEC.md docs/ARCHITECTURE.md core/agent_loop.py app/serializers.py tests/test_web_app.py -S` 결과도 `/work`가 말한 관련 필드 문서화를 뒷받침했습니다.
- 다만 `/work`의 `남은 리스크`는 current remaining gap을 완전히 다 적지는 못했습니다.
  - [`docs/PRODUCT_SPEC.md:256`](/home/xpdlqj/code/projectH/docs/PRODUCT_SPEC.md#L256)은 `rendered_as` enum 값 `fact_card / uncertain / not_rendered`와 `progress_state` enum 값 `improved / regressed / unchanged`를 모두 적고 있습니다.
  - 반면 [`docs/ARCHITECTURE.md:170`](/home/xpdlqj/code/projectH/docs/ARCHITECTURE.md#L170)은 `rendered_as`와 `progress_state` 필드 이름만 적고, shipped enum 값은 아직 적지 않습니다.
  - 이 차이는 코드에서도 실제 contract로 고정되어 있습니다. [`core/agent_loop.py:4137`](/home/xpdlqj/code/projectH/core/agent_loop.py#L4137), [`core/agent_loop.py:4143`](/home/xpdlqj/code/projectH/core/agent_loop.py#L4143), [`core/agent_loop.py:4145`](/home/xpdlqj/code/projectH/core/agent_loop.py#L4145), [`core/agent_loop.py:4147`](/home/xpdlqj/code/projectH/core/agent_loop.py#L4147)은 `rendered_as` 값을, [`core/agent_loop.py:4193`](/home/xpdlqj/code/projectH/core/agent_loop.py#L4193), [`core/agent_loop.py:4196`](/home/xpdlqj/code/projectH/core/agent_loop.py#L4196), [`core/agent_loop.py:4199`](/home/xpdlqj/code/projectH/core/agent_loop.py#L4199)은 `progress_state` 값을 고정합니다.
  - 따라서 `/work`의 “남은 리스크는 `rendered_as` enum omission” 설명은 방향은 맞았지만, 실제 남은 parity gap은 `progress_state`까지 포함합니다.
- 다음 exact slice는 `Docs ARCHITECTURE claim_coverage enum-value parity truth sync`로 고정했습니다.
  - 같은 family 안에서 남은 가장 작은 current-risk는 [`docs/ARCHITECTURE.md`](/home/xpdlqj/code/projectH/docs/ARCHITECTURE.md) 한 줄의 enum-value parity drift입니다.
  - 이는 one-file bounded docs slice로 닫히고, `web_search_history` 같은 다음 metadata family로 넘어가기 전에 현재 line-level contract drift를 먼저 닫는 편이 더 직접적입니다.
- `.pipeline/claude_handoff.md`도 위 판단에 맞춰 새 next slice 기준으로 갱신했습니다.

## 검증
- `sed -n '1,260p' work/4/8/2026-04-08-docs-product-spec-architecture-claim-coverage-progress-summary-field-shape-truth-sync.md`
- `sed -n '1,260p' verify/4/8/2026-04-08-docs-acceptance-criteria-focus-slot-explanation-terminology-normalization-verification.md`
- `sed -n '1,260p' .pipeline/claude_handoff.md`
- `nl -ba docs/PRODUCT_SPEC.md | sed -n '248,266p'`
- `nl -ba docs/ARCHITECTURE.md | sed -n '160,180p'`
- `git diff -- docs/PRODUCT_SPEC.md docs/ARCHITECTURE.md`
- `git diff --check`
- `rg -n "claim_coverage_progress_summary|previous_status|previous_status_label|progress_state|progress_label|is_focus_slot|rendered_as|support_count|candidate_count|status_label" docs/PRODUCT_SPEC.md docs/ARCHITECTURE.md core/agent_loop.py app/serializers.py tests/test_web_app.py -S`
- `rg -n "web_search_history|claim_coverage_progress_summary|claim_coverage" docs/PRODUCT_SPEC.md docs/ARCHITECTURE.md README.md docs/NEXT_STEPS.md docs/TASK_BACKLOG.md docs/ACCEPTANCE_CRITERIA.md -S`
- `nl -ba docs/PRODUCT_SPEC.md | sed -n '300,316p'`
- `nl -ba docs/ARCHITECTURE.md | sed -n '132,176p'`
- `nl -ba app/serializers.py | sed -n '944,962p'`
- `nl -ba core/agent_loop.py | sed -n '4132,4160p'`
- `nl -ba core/agent_loop.py | sed -n '4190,4200p'`
- `rg -n "fact_card|uncertain|not_rendered|improved|regressed|unchanged" docs/PRODUCT_SPEC.md docs/ARCHITECTURE.md -S`
- `git status --short`

## 남은 리스크
- [`docs/ARCHITECTURE.md:170`](/home/xpdlqj/code/projectH/docs/ARCHITECTURE.md#L170)은 `rendered_as`와 `progress_state` field names는 적고 있지만 shipped enum 값은 아직 적지 않아, [`docs/PRODUCT_SPEC.md:256`](/home/xpdlqj/code/projectH/docs/PRODUCT_SPEC.md#L256) 및 실제 코드와의 parity가 완전히 닫히지 않았습니다.
- `web_search_history` field-shape는 현재도 [`docs/PRODUCT_SPEC.md:258`](/home/xpdlqj/code/projectH/docs/PRODUCT_SPEC.md#L258), [`docs/ARCHITECTURE.md:172`](/home/xpdlqj/code/projectH/docs/ARCHITECTURE.md#L172)에서 이름만 적혀 있어 다음 metadata family로 남아 있지만, 이번 tie-break에서는 더 작은 same-family parity drift를 먼저 닫는 편이 맞다고 판단했습니다.
- unrelated dirty worktree(`.gitignore`, `.pipeline/README.md`, `AGENTS.md`, `CLAUDE.md`, `GEMINI.md`, `PROJECT_CUSTOM_INSTRUCTIONS.md`, `pipeline_gui/*`, `watcher_core.py`, 관련 tests, `work/README.md`, `verify/README.md`, `report/gemini/README.md`, 기타 unrelated `work/` / `verify/` note)는 이번 검증 범위 밖이라 손대지 않았습니다.
