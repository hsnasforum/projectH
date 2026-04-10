# Docs selected_source_paths non-null truth sync verification

## 변경 파일
- `verify/4/9/2026-04-09-docs-selected-source-paths-non-null-truth-sync-verification.md`
- `.pipeline/claude_handoff.md`

## 사용 skill
- `round-handoff`

## 변경 이유
- 최신 `/work` `work/4/9/2026-04-09-docs-selected-source-paths-non-null-truth-sync.md`가 직전 verification note가 고정한 response payload `selected_source_paths` drift를 실제로 닫았는지 다시 확인하고, 같은 top-level response payload docs family의 다음 단일 current-risk reduction 슬라이스를 좁힐 필요가 있었습니다.
- 같은 날짜의 기존 verification note `verify/4/9/2026-04-09-docs-content-metadata-field-nullability-truth-sync-verification.md`를 먼저 읽은 뒤, 그 후속 `/work`가 실제로 그 지적을 닫았는지 재검수했습니다.

## 핵심 변경
- 최신 `/work`는 truthful합니다.
  - `docs/PRODUCT_SPEC.md:305`는 이제 `selected_source_paths`를 `default []`, never `null`로 적고 있습니다.
  - `docs/ARCHITECTURE.md:152`도 `list` with `default []`로 같은 truth를 반영합니다.
- 이 문구는 shipped top-level response payload contract와 맞습니다.
  - response model은 `selected_source_paths: list[str] = field(default_factory=list)`로 고정됩니다 (`core/agent_loop.py:75`).
  - serializer는 값을 그대로 직렬화하고 `null` 변환이 없습니다 (`app/serializers.py:48`).
  - 이번 라운드에서 `selected_source_paths=None` 또는 동등한 할당 경로는 찾지 못했습니다 (`rg -n 'selected_source_paths\\s*=\\s*None|selected_source_paths=None' core app tests -S` 결과 없음).
  - focused tests도 top-level response payload에서 list를 잠급니다 (`tests/test_web_app.py:4612`, `tests/test_web_app.py:5773`).
- 이로써 `selected_source_paths` non-null drift는 닫혔습니다.
- 같은 top-level response payload family 안의 다음 smallest current-risk reduction은 `PRODUCT_SPEC` control path field nullability drift입니다.
  - `proposed_note_path`, `saved_note_path`, `web_search_record_path`는 response model에서 nullable입니다 (`core/agent_loop.py:73-74`, `core/agent_loop.py:85`).
  - serializer도 이 값을 그대로 노출합니다 (`app/serializers.py:45-47`).
  - shell은 모두 nullable/fallback path로 소비합니다 (`app/static/app.js:1070-1075`, `app/static/app.js:1693-1703`).
  - `docs/ARCHITECTURE.md:142-144`는 이미 `string | null`로 truthful하지만, `docs/PRODUCT_SPEC.md:291-293`은 아직 object/value-only처럼 읽힙니다.
- 다음 Claude 슬라이스는 `.pipeline/claude_handoff.md`에 `Docs PRODUCT_SPEC response payload control path field nullability truth sync`로 고정했습니다.

## 검증
- `sed -n '1,240p' .agents/skills/round-handoff/SKILL.md`
- `sed -n '1,260p' AGENTS.md`
- `sed -n '1,220p' work/README.md`
- `sed -n '1,220p' verify/README.md`
- `sed -n '1,220p' .pipeline/README.md`
- `sed -n '1,260p' work/4/9/2026-04-09-docs-selected-source-paths-non-null-truth-sync.md`
- `sed -n '1,260p' verify/4/9/2026-04-09-docs-content-metadata-field-nullability-truth-sync-verification.md`
- `sed -n '1,220p' docs/NEXT_STEPS.md`
- `sed -n '1,220p' docs/MILESTONES.md`
- `sed -n '1,220p' docs/TASK_BACKLOG.md`
- `git status --short`
- `git diff -- docs/PRODUCT_SPEC.md docs/ARCHITECTURE.md`
- `git diff --check`
- `rg -n '\bproposed_note_path\b|\bsaved_note_path\b|\bweb_search_record_path\b|\bfollow_up_suggestions\b|\bsearch_results\b' docs/PRODUCT_SPEC.md docs/ARCHITECTURE.md docs/ACCEPTANCE_CRITERIA.md app/serializers.py core/agent_loop.py app/static/app.js tests/test_web_app.py tests/test_smoke.py -S`
- `rg -n 'selected_source_paths\s*=\s*None|selected_source_paths=None' core app tests -S`
- `nl -ba docs/PRODUCT_SPEC.md | sed -n '287,316p'`
- `nl -ba docs/ARCHITECTURE.md | sed -n '140,160p'`
- `nl -ba app/serializers.py | sed -n '41,49p'`
- `nl -ba core/agent_loop.py | sed -n '70,86p'`
- `nl -ba app/static/app.js | sed -n '1068,1076p'`
- `nl -ba app/static/app.js | sed -n '1688,1704p'`
- `nl -ba tests/test_web_app.py | sed -n '4606,4615p'`
- `nl -ba tests/test_web_app.py | sed -n '5768,5780p'`
- `sed -n '1,240p' .pipeline/claude_handoff.md`
- `sed -n '1,200p' .pipeline/gemini_request.md`
- `sed -n '1,200p' .pipeline/operator_request.md`
- `ls -1 verify/4/9`

## 남은 리스크
- 이번 라운드는 docs/code truth 대조와 handoff 갱신만 수행했습니다. Python unit test와 Playwright는 재실행하지 않았습니다.
- `selected_source_paths` drift는 닫혔지만, `docs/PRODUCT_SPEC.md`의 top-level control field list는 아직 `proposed_note_path`, `saved_note_path`, `web_search_record_path`의 `null` 가능성을 직접 드러내지 않습니다.
- 현재 worktree에는 이 라운드와 무관한 dirty/untracked 파일이 많이 남아 있으므로 다음 슬라이스도 unrelated changes를 건드리지 말아야 합니다.
