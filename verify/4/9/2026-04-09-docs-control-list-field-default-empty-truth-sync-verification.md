# Docs control list field default-empty truth sync verification

## 변경 파일
- `verify/4/9/2026-04-09-docs-control-list-field-default-empty-truth-sync-verification.md`
- `.pipeline/claude_handoff.md`

## 사용 skill
- `round-handoff`

## 변경 이유
- 최신 `/work` `work/4/9/2026-04-09-docs-control-list-field-default-empty-truth-sync.md`가 직전 verification note가 고정한 response payload control-list default-empty drift를 실제로 닫았는지 다시 확인하고, 같은 top-level response payload docs family의 다음 단일 current-risk reduction 슬라이스를 좁힐 필요가 있었습니다.
- 같은 날짜의 기존 verification note `verify/4/9/2026-04-09-docs-control-path-field-nullability-truth-sync-verification.md`를 먼저 읽은 뒤, 그 후속 `/work`가 실제로 그 지적을 닫았는지 재검수했습니다.

## 핵심 변경
- 최신 `/work`는 truthful합니다.
  - `docs/PRODUCT_SPEC.md:289`, `docs/PRODUCT_SPEC.md:294-295`는 이제 `actions_taken`, `follow_up_suggestions`, `search_results`를 각각 `(default [], never null)`로 직접 설명합니다.
  - 이 문구는 shipped top-level response payload contract와 맞습니다.
    - response model은 세 필드를 모두 list default로 고정합니다 (`core/agent_loop.py:71`, `core/agent_loop.py:79`, `core/agent_loop.py:93`).
    - serializer도 payload를 list 형태로 유지합니다 (`app/serializers.py:43`, `app/serializers.py:52`, `app/serializers.py:66-73`).
    - 이번 라운드에서 `actions_taken=None`, `follow_up_suggestions=None`, `search_results=None` 할당 경로는 찾지 못했습니다 (`rg -n 'actions_taken\\s*=\\s*None|follow_up_suggestions\\s*=\\s*None|search_results\\s*=\\s*None' core app tests -S` 결과 없음).
    - shell은 배열 기준 경로와 `[]` 폴백으로 이 필드를 소비합니다 (`app/static/app.js:999-1010`, `app/static/app.js:3152`, `app/static/app.js:3182`, `app/static/app.js:3195`, `app/static/app.js:3214`).
    - focused tests도 list shape/value를 잠급니다 (`tests/test_web_app.py:4637`, `tests/test_web_app.py:5027`, `tests/test_web_app.py:5775-5780`).
- 이로써 response payload control-list default-empty drift는 닫혔습니다.
- 같은 top-level response payload family 안의 다음 smallest current-risk reduction은 `PRODUCT_SPEC` metadata/panel field empty-state drift입니다.
  - `evidence`, `summary_chunks`, `claim_coverage`는 response model에서 list default로 고정되고 (`core/agent_loop.py:81-83`), serializer helper도 빈 입력을 `[]`로 직렬화합니다 (`app/serializers.py:55-56`, `app/serializers.py:62`, `app/serializers.py:895-962`).
  - 이번 라운드에서 `evidence=None`, `summary_chunks=None`, `claim_coverage=None`, `claim_coverage_progress_summary=None` 할당 경로는 찾지 못했습니다 (`rg -n 'claim_coverage_progress_summary\\s*=\\s*None|evidence\\s*=\\s*None|summary_chunks\\s*=\\s*None|claim_coverage\\s*=\\s*None' core app tests -S` 결과 없음).
  - top-level response payload의 `claim_coverage_progress_summary`는 serializer에서 항상 localized string으로 내려가며, 값이 없으면 빈 문자열이 됩니다 (`core/agent_loop.py:84`, `app/serializers.py:63-65`).
  - shell도 panel 렌더링에서 `evidence`, `summary_chunks`, `claim_coverage`는 `[]`, `claim_coverage_progress_summary`는 `""` 폴백으로 소비합니다 (`app/static/app.js:3159-3165`, `app/static/app.js:3205-3211`).
  - focused tests는 top-level payload의 `evidence`, `claim_coverage`, `claim_coverage_progress_summary` shape를 잠그고, response object에서 빈 `summary_chunks`도 확인합니다 (`tests/test_web_app.py:4492-4501`, `tests/test_web_app.py:5288-5301`, `tests/test_web_app.py:5413`, `tests/test_smoke.py:3808`).
  - 하지만 `docs/PRODUCT_SPEC.md:312-315`는 아직 top-level payload 기준의 `[]` / `""` empty-state truth를 직접 닫지 않습니다.
- 다음 Claude 슬라이스는 `.pipeline/claude_handoff.md`에 `Docs PRODUCT_SPEC response payload metadata panel empty-state truth sync`로 고정했습니다.

## 검증
- `sed -n '1,220p' .agents/skills/round-handoff/SKILL.md`
- `sed -n '1,260p' AGENTS.md`
- `sed -n '1,220p' work/README.md`
- `sed -n '1,220p' verify/README.md`
- `sed -n '1,220p' .pipeline/README.md`
- `sed -n '1,260p' work/4/9/2026-04-09-docs-control-list-field-default-empty-truth-sync.md`
- `sed -n '1,260p' verify/4/9/2026-04-09-docs-control-path-field-nullability-truth-sync-verification.md`
- `sed -n '1,220p' docs/NEXT_STEPS.md`
- `sed -n '1,220p' docs/MILESTONES.md`
- `sed -n '1,220p' docs/TASK_BACKLOG.md`
- `git status --short`
- `git diff --check`
- `git diff -- docs/PRODUCT_SPEC.md`
- `nl -ba docs/PRODUCT_SPEC.md | sed -n '258,315p'`
- `nl -ba core/agent_loop.py | sed -n '70,95p'`
- `nl -ba app/serializers.py | sed -n '41,74p'`
- `nl -ba app/serializers.py | sed -n '892,970p'`
- `nl -ba docs/ARCHITECTURE.md | sed -n '152,162p'`
- `nl -ba docs/ACCEPTANCE_CRITERIA.md | sed -n '90,121p'`
- `nl -ba app/static/app.js | sed -n '3156,3212p'`
- `nl -ba tests/test_web_app.py | sed -n '4488,4502p'`
- `nl -ba tests/test_web_app.py | sed -n '5284,5302p'`
- `nl -ba tests/test_web_app.py | sed -n '5408,5445p'`
- `nl -ba tests/test_smoke.py | sed -n '1930,1955p'`
- `nl -ba tests/test_smoke.py | sed -n '3798,3812p'`
- `rg -n 'actions_taken|follow_up_suggestions|search_results' app/static/app.js tests/test_web_app.py tests/test_smoke.py -S`
- `rg -n '\\bevidence\\b|\\bsummary_chunks\\b|\\bclaim_coverage\\b|\\bclaim_coverage_progress_summary\\b' docs/PRODUCT_SPEC.md docs/ARCHITECTURE.md docs/ACCEPTANCE_CRITERIA.md app/serializers.py core/agent_loop.py tests/test_web_app.py tests/test_smoke.py app/static/app.js -S`
- `rg -n 'actions_taken\\s*=\\s*None|follow_up_suggestions\\s*=\\s*None|search_results\\s*=\\s*None' core app tests -S`
- `rg -n 'claim_coverage_progress_summary\\s*=\\s*None|evidence\\s*=\\s*None|summary_chunks\\s*=\\s*None|claim_coverage\\s*=\\s*None' core app tests -S`
- `sed -n '1,260p' .pipeline/claude_handoff.md`
- `sed -n '1,200p' .pipeline/gemini_request.md`
- `sed -n '1,200p' .pipeline/operator_request.md`

## 남은 리스크
- 이번 라운드는 docs/code truth 대조와 handoff 갱신만 수행했습니다. Python unit test와 Playwright는 재실행하지 않았습니다.
- `docs/PRODUCT_SPEC.md` top-level response payload metadata/panel field 설명은 아직 `evidence`, `summary_chunks`, `claim_coverage`, `claim_coverage_progress_summary`의 `[]` / `""` empty-state truth를 직접 적지 않아 다음 슬라이스가 남아 있습니다.
- 현재 worktree에는 이 라운드와 무관한 dirty/untracked 파일이 많이 남아 있으므로 다음 슬라이스도 unrelated changes를 건드리지 말아야 합니다.
