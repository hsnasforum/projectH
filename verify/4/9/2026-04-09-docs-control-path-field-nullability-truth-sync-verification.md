# Docs control path field nullability truth sync verification

## 변경 파일
- `verify/4/9/2026-04-09-docs-control-path-field-nullability-truth-sync-verification.md`
- `.pipeline/claude_handoff.md`

## 사용 skill
- `round-handoff`

## 변경 이유
- 최신 `/work` `work/4/9/2026-04-09-docs-control-path-field-nullability-truth-sync.md`가 직전 verification note가 고정한 response payload control-path nullability drift를 실제로 닫았는지 다시 확인하고, 같은 top-level response payload docs family의 다음 단일 current-risk reduction 슬라이스를 좁힐 필요가 있었습니다.
- 같은 날짜의 기존 verification note `verify/4/9/2026-04-09-docs-selected-source-paths-non-null-truth-sync-verification.md`를 먼저 읽은 뒤, 그 후속 `/work`가 실제로 그 지적을 닫았는지 재검수했습니다.

## 핵심 변경
- 최신 `/work`는 truthful합니다.
  - `docs/PRODUCT_SPEC.md:291-293`는 이제 `proposed_note_path`, `saved_note_path`, `web_search_record_path`를 각각 `null` 가능 형태로 직접 설명합니다.
  - 이 문구는 shipped top-level response payload contract와 맞습니다.
    - response model은 `proposed_note_path: str | None`, `saved_note_path: str | None`, `web_search_record_path: str | None`로 고정됩니다 (`core/agent_loop.py:73-74`, `core/agent_loop.py:85`).
    - serializer는 이 값을 그대로 노출합니다 (`app/serializers.py:45-47`).
    - shell은 nullable/fallback path로 소비합니다 (`app/static/app.js:1070-1075`, `app/static/app.js:1693-1703`).
  - `docs/ARCHITECTURE.md:142-144`도 이미 `string | null`로 같은 truth를 유지하고 있습니다.
- 이로써 response payload control-path nullability drift는 닫혔습니다.
- 같은 top-level response payload family 안의 다음 smallest current-risk reduction은 `PRODUCT_SPEC` control list field default-empty drift입니다.
  - `actions_taken`, `follow_up_suggestions`, `search_results`는 response model에서 모두 list로 고정됩니다 (`core/agent_loop.py:71`, `core/agent_loop.py:79`, `core/agent_loop.py:93`).
  - serializer도 payload를 list로 유지합니다 (`app/serializers.py:43`, `app/serializers.py:52`, `app/serializers.py:66-73`).
  - 이번 라운드에서 `actions_taken=None`, `follow_up_suggestions=None`, `search_results=None` 할당 경로는 찾지 못했습니다 (`rg -n 'actions_taken\\s*=\\s*None|follow_up_suggestions\\s*=\\s*None|search_results\\s*=\\s*None' core app tests -S` 결과 없음).
  - focused payload tests는 list shape/value를 잠급니다 (`tests/test_web_app.py:4637`, `tests/test_web_app.py:5027`, `tests/test_web_app.py:5775-5780`).
  - shell도 `search_results`와 `follow_up_suggestions`를 array 기준으로 렌더링합니다 (`app/static/app.js:999-1010`, `app/static/app.js:3152`, `app/static/app.js:3182`, `app/static/app.js:3195`, `app/static/app.js:3214`).
  - 하지만 `docs/PRODUCT_SPEC.md:289`, `docs/PRODUCT_SPEC.md:294-295`는 아직 `default []`, never `null` truth를 직접 닫지 않습니다.
- 다음 Claude 슬라이스는 `.pipeline/claude_handoff.md`에 `Docs PRODUCT_SPEC response payload control list field default-empty truth sync`로 고정했습니다.

## 검증
- `sed -n '1,240p' .agents/skills/round-handoff/SKILL.md`
- `sed -n '1,260p' AGENTS.md`
- `sed -n '1,220p' work/README.md`
- `sed -n '1,220p' verify/README.md`
- `sed -n '1,220p' .pipeline/README.md`
- `sed -n '1,260p' work/4/9/2026-04-09-docs-control-path-field-nullability-truth-sync.md`
- `sed -n '1,260p' verify/4/9/2026-04-09-docs-selected-source-paths-non-null-truth-sync-verification.md`
- `sed -n '1,220p' docs/NEXT_STEPS.md`
- `sed -n '1,220p' docs/MILESTONES.md`
- `sed -n '1,220p' docs/TASK_BACKLOG.md`
- `git status --short`
- `git diff -- docs/PRODUCT_SPEC.md docs/ARCHITECTURE.md`
- `git diff --check`
- `nl -ba docs/PRODUCT_SPEC.md | sed -n '287,296p'`
- `nl -ba docs/PRODUCT_SPEC.md | sed -n '296,316p'`
- `nl -ba docs/ARCHITECTURE.md | sed -n '140,160p'`
- `nl -ba core/agent_loop.py | sed -n '70,95p'`
- `nl -ba app/serializers.py | sed -n '41,74p'`
- `nl -ba tests/test_web_app.py | sed -n '4628,4639p'`
- `nl -ba tests/test_web_app.py | sed -n '5018,5030p'`
- `nl -ba tests/test_web_app.py | sed -n '5768,5792p'`
- `rg -n '\\bproposed_note_path\\b|\\bsaved_note_path\\b|\\bweb_search_record_path\\b|\\bfollow_up_suggestions\\b|\\bsearch_results\\b' docs/PRODUCT_SPEC.md docs/ARCHITECTURE.md docs/ACCEPTANCE_CRITERIA.md app/serializers.py core/agent_loop.py app/static/app.js tests/test_web_app.py tests/test_smoke.py -S`
- `rg -n '\\bevidence\\b|\\bsummary_chunks\\b|\\bclaim_coverage\\b|\\bactions_taken\\b|\\bfollow_up_suggestions\\b|\\bsearch_results\\b' docs/PRODUCT_SPEC.md docs/ARCHITECTURE.md docs/ACCEPTANCE_CRITERIA.md -S`
- `rg -n 'actions_taken\\s*=\\s*None|follow_up_suggestions\\s*=\\s*None|search_results\\s*=\\s*None' core app tests -S`
- `rg -n 'follow_up_suggestions|search_results|actions_taken' app/static/app.js -S`
- `sed -n '1,220p' .pipeline/claude_handoff.md`
- `sed -n '1,200p' .pipeline/gemini_request.md`
- `sed -n '1,200p' .pipeline/operator_request.md`
- `ls -1 verify/4/9`

## 남은 리스크
- 이번 라운드는 docs/code truth 대조와 handoff 갱신만 수행했습니다. Python unit test와 Playwright는 재실행하지 않았습니다.
- `docs/PRODUCT_SPEC.md` top-level response payload control list field 설명은 아직 `actions_taken`, `follow_up_suggestions`, `search_results`의 default-empty / non-null truth를 직접 적지 않아 다음 슬라이스가 남아 있습니다.
- 현재 worktree에는 이 라운드와 무관한 dirty/untracked 파일이 많이 남아 있으므로 다음 슬라이스도 unrelated changes를 건드리지 말아야 합니다.
