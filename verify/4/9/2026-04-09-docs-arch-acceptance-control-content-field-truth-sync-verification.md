# Docs arch acceptance control content field truth sync verification

## 변경 파일
- `verify/4/9/2026-04-09-docs-arch-acceptance-control-content-field-truth-sync-verification.md`
- `.pipeline/claude_handoff.md`

## 사용 skill
- `round-handoff`

## 변경 이유
- 최신 `/work` `work/4/9/2026-04-09-docs-arch-acceptance-control-content-field-truth-sync.md`가 직전 verification note가 고정한 `ARCHITECTURE` + `ACCEPTANCE_CRITERIA` response payload control/content field drift를 실제로 닫았는지 다시 확인하고, 같은 response payload docs family의 다음 단일 current-risk reduction 슬라이스를 좁힐 필요가 있었습니다.
- 같은 날짜의 기존 verification note `verify/4/9/2026-04-09-docs-arch-acceptance-metadata-panel-empty-state-truth-sync-verification.md`를 먼저 읽은 뒤, 그 후속 `/work`가 실제로 그 지적을 닫았는지 재검수했습니다.

## 핵심 변경
- 최신 `/work`는 truthful합니다.
  - `docs/ARCHITECTURE.md:140-146`은 이제 `actions_taken`, `follow_up_suggestions`, `search_results`의 default `[]`와 path field nullability를 직접 적습니다.
  - `docs/ARCHITECTURE.md:151-152`도 `note_preview` nullable, `selected_source_paths` default `[]`를 반영합니다.
  - `docs/ACCEPTANCE_CRITERIA.md:116-118`은 같은 top-level response payload control/content truth를 nullable/default-empty 주석으로 맞췄습니다.
- 이 문구는 shipped response payload contract와 맞습니다.
  - response model은 `proposed_note_path`, `saved_note_path`, `note_preview`, `web_search_record_path`를 nullable로 두고, `actions_taken`, `selected_source_paths`, `follow_up_suggestions`, `search_results`는 default-empty list로 둡니다 (`core/agent_loop.py:71-85`, `core/agent_loop.py:93`).
  - serializer도 같은 필드를 top-level response payload에 그대로 싣습니다 (`app/serializers.py:43-49`, `app/serializers.py:52`, `app/serializers.py:66-73`).
  - shell과 focused tests도 이 truth를 이미 소비하거나 잠급니다 (`app/static/app.js:1668-1675`, `app/static/app.js:3204-3214`, `tests/test_web_app.py:4612`, `tests/test_web_app.py:4637`, `tests/test_web_app.py:5027`, `tests/test_web_app.py:5773-5778`).
- 같은 response payload family 안의 다음 smallest current-risk reduction은 `ACCEPTANCE_CRITERIA` correction field truth sync입니다.
  - `docs/PRODUCT_SPEC.md:317-322`와 `docs/ARCHITECTURE.md:161-165`는 이미 `original_response_snapshot`, `corrected_outcome`, `approval_reason_record`, `content_reason_record`, `save_content_source`의 `null when absent` truth를 적고 있습니다.
  - 하지만 `docs/ACCEPTANCE_CRITERIA.md:120`은 correction fields를 generic list로만 적고 있어, `docs/ACCEPTANCE_CRITERIA.md:115`의 fixed-set response payload 설명과 함께 읽으면 아직 always-present value/object처럼 오해될 수 있습니다.
  - shipped serializer는 이 correction fields를 top-level response payload에 항상 포함하되 값이 없으면 `null`로 직렬화합니다 (`app/serializers.py:57-61`, `app/serializers.py:347-418`).
  - response model도 `original_response_snapshot`, `corrected_outcome`, `approval_reason_record`, `save_content_source`를 nullable로 둡니다 (`core/agent_loop.py:88-92`), `content_reason_record`도 serializer helper 기준으로 dict가 아니면 `null`입니다 (`app/serializers.py:413-418`).
  - focused test도 `original_response_snapshot`과 `corrected_outcome`의 top-level `null` 경로를 잠급니다 (`tests/test_web_app.py:6191-6192`).
- 다음 Claude 슬라이스는 `.pipeline/claude_handoff.md`에 `Docs ACCEPTANCE_CRITERIA response payload correction field nullability truth sync`로 고정했습니다.

## 검증
- `sed -n '1,240p' .agents/skills/round-handoff/SKILL.md`
- `sed -n '1,260p' AGENTS.md`
- `sed -n '1,220p' work/README.md`
- `sed -n '1,220p' verify/README.md`
- `sed -n '1,220p' .pipeline/README.md`
- `sed -n '1,220p' work/4/9/2026-04-09-docs-arch-acceptance-control-content-field-truth-sync.md`
- `sed -n '1,220p' verify/4/9/2026-04-09-docs-arch-acceptance-metadata-panel-empty-state-truth-sync-verification.md`
- `sed -n '1,220p' docs/NEXT_STEPS.md`
- `sed -n '1,220p' docs/MILESTONES.md`
- `sed -n '1,220p' docs/TASK_BACKLOG.md`
- `git status --short`
- `git diff -- docs/ARCHITECTURE.md docs/ACCEPTANCE_CRITERIA.md`
- `git diff --check`
- `rg -n 'selected_source_paths|note_preview|actions_taken|follow_up_suggestions|search_results|evidence|summary_chunks|claim_coverage|claim_coverage_progress_summary|proposed_note_path|saved_note_path|web_search_record_path' docs/ARCHITECTURE.md docs/ACCEPTANCE_CRITERIA.md docs/PRODUCT_SPEC.md -S`
- `rg -n 'actions_taken\\s*=\\s*None|follow_up_suggestions\\s*=\\s*None|search_results\\s*=\\s*None|selected_source_paths\\s*=\\s*None|note_preview\\s*=\\s*None' core app tests -S`
- `rg -n 'original_response_snapshot|corrected_outcome|approval_reason_record|content_reason_record|save_content_source' app/static/app.js tests/test_web_app.py tests/test_smoke.py docs/ARCHITECTURE.md docs/ACCEPTANCE_CRITERIA.md docs/PRODUCT_SPEC.md -S`
- `rg -n 'response payload|original_response_snapshot|corrected_outcome|approval_reason_record|content_reason_record|save_content_source' docs/ACCEPTANCE_CRITERIA.md -S`
- `rg -n 'content_reason_record' core/agent_loop.py app/serializers.py tests/test_web_app.py tests/test_smoke.py -S`
- `nl -ba docs/ARCHITECTURE.md | sed -n '139,165p'`
- `nl -ba docs/ACCEPTANCE_CRITERIA.md | sed -n '116,121p'`
- `nl -ba docs/PRODUCT_SPEC.md | sed -n '317,323p'`
- `nl -ba core/agent_loop.py | sed -n '71,93p'`
- `nl -ba app/serializers.py | sed -n '43,73p'`
- `nl -ba app/serializers.py | sed -n '347,418p'`
- `nl -ba app/static/app.js | sed -n '1668,1675p'`
- `nl -ba app/static/app.js | sed -n '3204,3214p'`
- `nl -ba tests/test_web_app.py | sed -n '4608,4614p'`
- `nl -ba tests/test_web_app.py | sed -n '5771,5778p'`
- `nl -ba tests/test_web_app.py | sed -n '6187,6193p'`
- `sed -n '1,220p' .pipeline/claude_handoff.md`
- `sed -n '1,200p' .pipeline/gemini_request.md`
- `sed -n '1,200p' .pipeline/operator_request.md`
- `ls -1 verify/4/9`
- `ls -1 work/4/9`

## 남은 리스크
- 이번 라운드는 docs/code truth 대조와 handoff 갱신만 수행했습니다. Python unit test와 Playwright는 재실행하지 않았습니다.
- `docs/ACCEPTANCE_CRITERIA.md`의 top-level response payload correction field line은 아직 `null when absent`와 `save_content_source = original_draft | corrected_text | null`을 직접 잠그지 못합니다.
- 현재 worktree에는 이 라운드와 무관한 dirty/untracked 파일이 많이 남아 있으므로 다음 슬라이스도 unrelated changes를 건드리지 말아야 합니다.
