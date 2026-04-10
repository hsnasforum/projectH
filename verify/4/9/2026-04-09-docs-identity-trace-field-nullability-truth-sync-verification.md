# Docs identity trace field nullability truth sync verification

## 변경 파일
- `verify/4/9/2026-04-09-docs-identity-trace-field-nullability-truth-sync-verification.md`
- `.pipeline/claude_handoff.md`

## 사용 skill
- `round-handoff`

## 변경 이유
- 최신 `/work` `work/4/9/2026-04-09-docs-identity-trace-field-nullability-truth-sync.md`가 직전 verification note가 고정한 `PRODUCT_SPEC` response payload identity/trace field nullability drift를 실제로 닫았는지 다시 확인하고, 같은 response payload docs family의 다음 단일 current-risk reduction 슬라이스를 좁힐 필요가 있었습니다.
- 같은 날짜의 기존 verification note `verify/4/9/2026-04-09-docs-correction-reason-field-nullability-truth-sync-verification.md`를 먼저 읽은 뒤, 그 후속 `/work`가 실제로 그 handoff를 닫았는지 재검수했습니다.

## 핵심 변경
- 최신 `/work`는 truthful합니다. `docs/PRODUCT_SPEC.md:297-300`은 이제 shipped top-level response payload identity/trace contract와 맞습니다.
  - `artifact_id`, `artifact_kind`, `source_message_id`는 response model에서 nullable입니다 (`core/agent_loop.py:69`, `core/agent_loop.py:86-87`).
  - serializer도 이 필드들을 그대로 `null` 가능 형태로 내보냅니다 (`app/serializers.py:36-40`, `app/serializers.py:390-394`).
  - 실제 error/system paths 중 일부는 이 앵커 없이 `AgentResponse`를 반환합니다 (`core/agent_loop.py:391-395`, `core/agent_loop.py:399-403`, `core/agent_loop.py:8775-8794`).
- 이로써 top-level response payload identity/trace nullability family는 닫혔습니다.
  - `docs/ARCHITECTURE.md:147-149`는 이미 `string | null`로 truthful했고,
  - 이번 `/work`가 `docs/PRODUCT_SPEC.md:297-300`도 같은 truth로 맞췄습니다.
- 같은 response payload section 안의 다음 smallest current-risk reduction은 `PRODUCT_SPEC`의 남은 nullable content/metadata field drift입니다.
  - `note_preview`, `approval`, `active_context`, `applied_preferences`는 shipped response contract에서 nullable입니다 (`core/agent_loop.py:76-78`, `core/agent_loop.py:90`).
  - serializer는 각각 `None` 또는 nullable helper를 그대로 노출합니다 (`app/serializers.py:49-54`, `app/serializers.py:300-320`).
  - shell도 이 부재 상태를 전제로 fallback/null path를 소비합니다 (`app/static/app.js:3181-3183`, `app/static/app.js:3212-3214`, `app/static/app.js:3218-3224`).
  - `docs/ARCHITECTURE.md:151-156`는 이미 truthful하지만, `docs/PRODUCT_SPEC.md:303-311`은 아직 object/value-only처럼 읽힙니다.
- 다음 Claude 슬라이스는 `.pipeline/claude_handoff.md`에 `Docs PRODUCT_SPEC response payload note_preview approval active_context applied_preferences nullability truth sync`로 고정했습니다.

## 검증
- `sed -n '1,260p' .agents/skills/round-handoff/SKILL.md`
- `sed -n '1,260p' AGENTS.md`
- `sed -n '1,220p' work/README.md`
- `sed -n '1,220p' verify/README.md`
- `sed -n '1,220p' .pipeline/README.md`
- `sed -n '1,260p' work/4/9/2026-04-09-docs-identity-trace-field-nullability-truth-sync.md`
- `sed -n '1,260p' verify/4/9/2026-04-09-docs-correction-reason-field-nullability-truth-sync-verification.md`
- `sed -n '1,220p' docs/NEXT_STEPS.md`
- `sed -n '1,220p' docs/MILESTONES.md`
- `sed -n '1,220p' docs/TASK_BACKLOG.md`
- `git status --short`
- `git diff -- docs/PRODUCT_SPEC.md`
- `git diff --check`
- `rg -n '\bartifact_id\b|\bartifact_kind\b|\bsource_message_id\b' docs/PRODUCT_SPEC.md docs/ARCHITECTURE.md docs/ACCEPTANCE_CRITERIA.md app/serializers.py core/agent_loop.py tests/test_web_app.py tests/test_smoke.py -S`
- `rg -n '\bselected_source_paths\b|\bnote_preview\b|\bapproval\b|\bactive_context\b|\bresponse_origin\b|\bapplied_preferences\b|\bclaim_coverage_progress_summary\b' docs/PRODUCT_SPEC.md docs/ARCHITECTURE.md docs/ACCEPTANCE_CRITERIA.md -S`
- `rg -n 'note_preview|approval|active_context|applied_preferences' app/static/app.js -S`
- `nl -ba docs/PRODUCT_SPEC.md | sed -n '280,340p'`
- `nl -ba docs/ARCHITECTURE.md | sed -n '140,175p'`
- `nl -ba docs/ACCEPTANCE_CRITERIA.md | sed -n '88,106p'`
- `nl -ba docs/ACCEPTANCE_CRITERIA.md | sed -n '112,130p'`
- `nl -ba app/serializers.py | sed -n '1,80p'`
- `nl -ba app/serializers.py | sed -n '296,340p'`
- `nl -ba app/serializers.py | sed -n '390,394p'`
- `nl -ba core/agent_loop.py | sed -n '66,92p'`
- `nl -ba core/agent_loop.py | sed -n '388,405p'`
- `nl -ba core/agent_loop.py | sed -n '8774,8794p'`
- `nl -ba app/static/app.js | sed -n '3120,3215p'`
- `sed -n '1,220p' .pipeline/claude_handoff.md`
- `sed -n '1,200p' .pipeline/gemini_request.md`
- `sed -n '1,200p' .pipeline/operator_request.md`
- `ls -1 verify/4/9`

## 남은 리스크
- 이번 라운드는 docs/code truth 대조와 handoff 갱신만 수행했습니다. Python unit test와 Playwright는 재실행하지 않았습니다.
- response payload identity/trace nullability family는 닫혔지만, `docs/PRODUCT_SPEC.md`의 같은 top-level field list에는 `note_preview`, `approval`, `active_context`, `applied_preferences`의 `null` 가능성이 아직 직접 드러나지 않습니다.
- 현재 worktree에는 이 라운드와 무관한 dirty/untracked 파일이 많이 남아 있으므로 다음 슬라이스도 unrelated changes를 건드리지 말아야 합니다.
