# Docs content metadata field nullability truth sync verification

## 변경 파일
- `verify/4/9/2026-04-09-docs-content-metadata-field-nullability-truth-sync-verification.md`
- `.pipeline/claude_handoff.md`

## 사용 skill
- `round-handoff`

## 변경 이유
- 최신 `/work` `work/4/9/2026-04-09-docs-content-metadata-field-nullability-truth-sync.md`가 직전 verification note가 고정한 `PRODUCT_SPEC` response payload content/metadata field nullability drift를 실제로 닫았는지 다시 확인하고, 같은 response payload docs family의 다음 단일 current-risk reduction 슬라이스를 좁힐 필요가 있었습니다.
- 같은 날짜의 기존 verification note `verify/4/9/2026-04-09-docs-identity-trace-field-nullability-truth-sync-verification.md`를 먼저 읽은 뒤, 그 후속 `/work`가 실제로 그 handoff를 닫았는지 재검수했습니다.

## 핵심 변경
- 최신 `/work`는 부분적으로만 truthful합니다.
  - `note_preview`, `approval`, `active_context`, `applied_preferences`에 대한 nullable 문구는 shipped response contract와 맞습니다 (`docs/PRODUCT_SPEC.md:304`, `docs/PRODUCT_SPEC.md:308-311` vs `core/agent_loop.py:76-78`, `core/agent_loop.py:90`, `app/serializers.py:49-54`, `app/serializers.py:300-320`, `app/static/app.js:3212-3214`, `app/static/app.js:3219-3224`).
  - 하지만 `selected_source_paths`를 `or null`로 바꾼 부분은 top-level response payload truth와 맞지 않습니다 (`docs/PRODUCT_SPEC.md:305`).
- shipped top-level response payload에서 `selected_source_paths`는 `null`이 아니라 non-null list입니다.
  - response model은 `selected_source_paths: list[str] = field(default_factory=list)`로 고정됩니다 (`core/agent_loop.py:75`).
  - serializer는 그 값을 그대로 내보냅니다 (`app/serializers.py:48`).
  - 이번 라운드에서 `selected_source_paths=None` 또는 동등한 설정 경로는 찾지 못했습니다 (`rg -n 'selected_source_paths\\s*=\\s*None|selected_source_paths=None|AgentResponse\\([^\\)]*selected_source_paths\\s*=\\s*None' core app tests -S` 결과 없음).
  - focused tests도 top-level response payload에서 list를 잠급니다 (`tests/test_web_app.py:4612`, `tests/test_web_app.py:5773`).
- 따라서 response payload content/metadata nullability family는 아직 닫히지 않았습니다.
  - `docs/PRODUCT_SPEC.md:305`의 `selected_source_paths ... or null`은 untruthful합니다.
  - `docs/ARCHITECTURE.md:152`도 아직 `list | null`로 적혀 있어 같은 drift를 유지합니다.
  - 반면 `docs/ACCEPTANCE_CRITERIA.md:118`은 neutral wording이라 이번 mismatch를 직접 만들지 않습니다.
- 다음 Claude 슬라이스는 `.pipeline/claude_handoff.md`에 `Docs PRODUCT_SPEC ARCHITECTURE response payload selected_source_paths non-null list truth sync`로 고정했습니다.

## 검증
- `sed -n '1,260p' .agents/skills/round-handoff/SKILL.md`
- `sed -n '1,260p' AGENTS.md`
- `sed -n '1,220p' work/README.md`
- `sed -n '1,220p' verify/README.md`
- `sed -n '1,220p' .pipeline/README.md`
- `sed -n '1,260p' work/4/9/2026-04-09-docs-content-metadata-field-nullability-truth-sync.md`
- `sed -n '1,260p' verify/4/9/2026-04-09-docs-identity-trace-field-nullability-truth-sync-verification.md`
- `sed -n '1,220p' docs/NEXT_STEPS.md`
- `sed -n '1,220p' docs/MILESTONES.md`
- `sed -n '1,220p' docs/TASK_BACKLOG.md`
- `git status --short`
- `git diff -- docs/PRODUCT_SPEC.md`
- `git diff --check`
- `rg -n '\bnote_preview\b|\bselected_source_paths\b|\bapproval\b|\bactive_context\b|\bapplied_preferences\b|\bclaim_coverage_progress_summary\b|\bweb_search_record_path\b|\bsaved_note_path\b|\bfollow_up_suggestions\b|\bsearch_results\b' docs/PRODUCT_SPEC.md docs/ARCHITECTURE.md docs/ACCEPTANCE_CRITERIA.md app/serializers.py core/agent_loop.py app/static/app.js tests/test_web_app.py tests/test_smoke.py -S`
- `rg -n 'selected_source_paths\s*=\s*None|selected_source_paths=None|AgentResponse\([^\)]*selected_source_paths\s*=\s*None' core app tests -S`
- `rg -n 'selected_source_paths' core/agent_loop.py app/serializers.py tests/test_web_app.py tests/test_smoke.py -S`
- `nl -ba docs/PRODUCT_SPEC.md | sed -n '300,316p'`
- `nl -ba docs/ARCHITECTURE.md | sed -n '150,160p'`
- `nl -ba docs/ACCEPTANCE_CRITERIA.md | sed -n '114,121p'`
- `nl -ba app/serializers.py | sed -n '45,55p'`
- `nl -ba app/serializers.py | sed -n '300,320p'`
- `nl -ba core/agent_loop.py | sed -n '74,90p'`
- `nl -ba core/agent_loop.py | sed -n '7348,7403p'`
- `nl -ba app/static/app.js | sed -n '3180,3224p'`
- `nl -ba tests/test_web_app.py | sed -n '4606,4615p'`
- `nl -ba tests/test_web_app.py | sed -n '5768,5780p'`
- `sed -n '1,260p' .pipeline/claude_handoff.md`
- `ls -1 verify/4/9`

## 남은 리스크
- 이번 라운드는 docs/code truth 대조와 handoff 갱신만 수행했습니다. Python unit test와 Playwright는 재실행하지 않았습니다.
- 최신 `/work`가 `note_preview`, `approval`, `active_context`, `applied_preferences`는 맞췄지만, `selected_source_paths`를 nullable로 적어 response payload family를 완전히 닫지는 못했습니다.
- 현재 worktree에는 이 라운드와 무관한 dirty/untracked 파일이 많이 남아 있으므로 다음 슬라이스도 unrelated changes를 건드리지 말아야 합니다.
