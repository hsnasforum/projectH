# Docs ARCHITECTURE ACCEPTANCE metadata panel empty-state truth sync verification

## 변경 파일
- `verify/4/9/2026-04-09-docs-arch-acceptance-metadata-panel-empty-state-truth-sync-verification.md`
- `.pipeline/claude_handoff.md`

## 사용 skill
- `round-handoff`

## 변경 이유
- 최신 `/work` `work/4/9/2026-04-09-docs-arch-acceptance-metadata-panel-empty-state-truth-sync.md`가 직전 verification note가 고정한 `ARCHITECTURE` / `ACCEPTANCE_CRITERIA` response payload metadata/panel empty-state drift를 실제로 닫았는지 다시 확인하고, 같은 top-level response payload docs family의 다음 단일 current-risk reduction 슬라이스를 좁힐 필요가 있었습니다.
- 같은 날짜의 기존 verification note `verify/4/9/2026-04-09-docs-metadata-panel-empty-state-truth-sync-verification.md`를 먼저 읽은 뒤, 그 후속 `/work`가 실제로 그 지적을 닫았는지 재검수했습니다.

## 핵심 변경
- 최신 `/work`는 truthful합니다.
  - `docs/ARCHITECTURE.md:157-160`는 이제 response-level `evidence`, `summary_chunks`, `claim_coverage`, `claim_coverage_progress_summary`에 `default []` / `default ""`를 직접 적습니다.
  - `docs/ACCEPTANCE_CRITERIA.md:119`도 같은 response-level metadata fields에 `nullable`, `default []`, `default ""` 주석을 추가해 `PRODUCT_SPEC`와 맞춥니다.
  - 이 문구는 shipped top-level response payload contract와 맞습니다.
    - response model은 `evidence`, `summary_chunks`, `claim_coverage`를 list default로 고정하고 `claim_coverage_progress_summary`는 nullable internal field로 둡니다 (`core/agent_loop.py:81-84`).
    - top-level serializer는 세 panel list 필드를 list로 직렬화하고 progress summary는 빈 값일 때 `""`로 내립니다 (`app/serializers.py:55-65`, `app/serializers.py:895-962`).
    - shell은 response/session 렌더링에서 `[]` / `""` 폴백으로 소비합니다 (`app/static/app.js:3159-3178`, `app/static/app.js:3205-3211`).
    - focused tests도 top-level payload shape를 잠급니다 (`tests/test_web_app.py:4492-4501`, `tests/test_web_app.py:5413`).
- 이로써 top-level response payload metadata/panel empty-state truth는 `PRODUCT_SPEC`, `ARCHITECTURE`, `ACCEPTANCE_CRITERIA` 세 canonical docs에서 닫혔습니다.
- 같은 top-level response payload family 안의 다음 smallest coherent current-risk reduction은 `ARCHITECTURE` + `ACCEPTANCE_CRITERIA` control/content field truth sync입니다.
  - `docs/ARCHITECTURE.md:140`, `docs/ARCHITECTURE.md:145-146`은 아직 `actions_taken`, `follow_up_suggestions`, `search_results`를 generic list로만 적고 있어 shipped default `[]` truth를 직접 드러내지 않습니다.
  - `docs/ACCEPTANCE_CRITERIA.md:116`은 shell control fields를 묶어 적지만 `actions_taken` / `follow_up_suggestions` / `search_results`의 default `[]`와 `proposed_note_path` / `saved_note_path` / `web_search_record_path`의 nullable truth를 직접 적지 않습니다.
  - `docs/ACCEPTANCE_CRITERIA.md:118`도 `note_preview` nullable, `selected_source_paths` default `[]` truth를 top-level payload 기준으로 직접 적지 않습니다.
  - 실제 shipped contract는 top-level response model과 serializer에서 이미 고정됩니다 (`core/agent_loop.py:71-76`, `core/agent_loop.py:79`, `core/agent_loop.py:85`, `core/agent_loop.py:93`, `app/serializers.py:43-49`, `app/serializers.py:52`, `app/serializers.py:66-73`).
  - shell과 focused tests도 이 control/content semantics를 소비하거나 잠급니다 (`app/static/app.js:999-1010`, `app/static/app.js:1670-1674`, `app/static/app.js:3195`, `app/static/app.js:3204`, `app/static/app.js:3212`, `app/static/app.js:3214`, `tests/test_web_app.py:4612`, `tests/test_web_app.py:4637`, `tests/test_web_app.py:5027`, `tests/test_web_app.py:5773-5778`).
- 다음 Claude 슬라이스는 `.pipeline/claude_handoff.md`에 `Docs ARCHITECTURE ACCEPTANCE_CRITERIA response payload control content field truth sync`로 고정했습니다.

## 검증
- `sed -n '1,220p' .agents/skills/round-handoff/SKILL.md`
- `sed -n '1,260p' AGENTS.md`
- `sed -n '1,220p' work/README.md`
- `sed -n '1,220p' verify/README.md`
- `sed -n '1,220p' .pipeline/README.md`
- `sed -n '1,260p' work/4/9/2026-04-09-docs-arch-acceptance-metadata-panel-empty-state-truth-sync.md`
- `sed -n '1,260p' verify/4/9/2026-04-09-docs-metadata-panel-empty-state-truth-sync-verification.md`
- `sed -n '1,220p' docs/NEXT_STEPS.md`
- `sed -n '1,220p' docs/MILESTONES.md`
- `sed -n '1,220p' docs/TASK_BACKLOG.md`
- `git status --short`
- `git diff --check`
- `git diff -- docs/ARCHITECTURE.md docs/ACCEPTANCE_CRITERIA.md`
- `nl -ba docs/ARCHITECTURE.md | sed -n '139,153p'`
- `nl -ba docs/ARCHITECTURE.md | sed -n '152,161p'`
- `nl -ba docs/ACCEPTANCE_CRITERIA.md | sed -n '114,121p'`
- `nl -ba core/agent_loop.py | sed -n '71,93p'`
- `nl -ba app/serializers.py | sed -n '43,49p'`
- `nl -ba app/serializers.py | sed -n '52,73p'`
- `nl -ba app/serializers.py | sed -n '55,65p'`
- `nl -ba app/serializers.py | sed -n '895,962p'`
- `nl -ba app/static/app.js | sed -n '1668,1675p'`
- `nl -ba app/static/app.js | sed -n '3158,3211p'`
- `nl -ba tests/test_web_app.py | sed -n '4490,4501p'`
- `nl -ba tests/test_web_app.py | sed -n '4608,4614p'`
- `nl -ba tests/test_web_app.py | sed -n '5408,5414p'`
- `nl -ba tests/test_web_app.py | sed -n '5771,5778p'`
- `rg -n 'selected_source_paths|note_preview|actions_taken|follow_up_suggestions|search_results|evidence|summary_chunks|claim_coverage|claim_coverage_progress_summary|proposed_note_path|saved_note_path|web_search_record_path' docs/ARCHITECTURE.md docs/ACCEPTANCE_CRITERIA.md docs/PRODUCT_SPEC.md -S`
- `rg -n 'actions_taken|follow_up_suggestions|search_results' app/static/app.js tests/test_web_app.py tests/test_smoke.py -S`
- `rg -n 'note_preview|selected_source_paths' app/static/app.js tests/test_web_app.py tests/test_smoke.py -S`
- `rg -n 'actions_taken\\s*=\\s*None|follow_up_suggestions\\s*=\\s*None|search_results\\s*=\\s*None|selected_source_paths\\s*=\\s*None|note_preview\\s*=\\s*None' core app tests -S`
- `sed -n '1,280p' .pipeline/claude_handoff.md`
- `sed -n '1,200p' .pipeline/gemini_request.md`
- `sed -n '1,200p' .pipeline/operator_request.md`

## 남은 리스크
- 이번 라운드는 docs/code truth 대조와 handoff 갱신만 수행했습니다. Python unit test와 Playwright는 재실행하지 않았습니다.
- metadata/panel empty-state family는 닫혔지만, 같은 top-level response payload family의 control/content field truth가 `docs/ARCHITECTURE.md`와 `docs/ACCEPTANCE_CRITERIA.md`에는 아직 partially generic wording으로 남아 있습니다.
- 현재 worktree에는 이 라운드와 무관한 dirty/untracked 파일이 많이 남아 있으므로 다음 슬라이스도 unrelated changes를 건드리지 말아야 합니다.
