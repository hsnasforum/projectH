# Docs correction reason field nullability truth sync verification

## 변경 파일
- `verify/4/9/2026-04-09-docs-correction-reason-field-nullability-truth-sync-verification.md`
- `.pipeline/claude_handoff.md`

## 사용 skill
- `round-handoff`

## 변경 이유
- 최신 `/work` `work/4/9/2026-04-09-docs-correction-reason-field-nullability-truth-sync.md`가 직전 verification note가 고정한 `PRODUCT_SPEC` response payload correction/reason field nullability drift를 실제로 닫았는지 다시 확인하고, 같은 response payload docs family의 다음 단일 current-risk reduction 슬라이스를 좁힐 필요가 있었습니다.
- 같은 날짜의 기존 verification note `verify/4/9/2026-04-09-docs-snapshot-response-origin-nullable-truth-sync-verification.md`를 먼저 읽은 뒤, 그 후속 `/work`가 실제로 그 지적을 닫았는지 재검수했습니다.

## 핵심 변경
- 최신 `/work`는 truthful합니다. `docs/PRODUCT_SPEC.md:317-322`는 이제 shipped top-level response payload contract와 맞습니다.
  - `app/serializers.py:57-61`은 response payload에 `original_response_snapshot`, `corrected_outcome`, `approval_reason_record`, `content_reason_record`, `save_content_source`를 항상 싣습니다.
  - 각 serializer helper는 값이 없으면 `None`을 반환합니다 (`app/serializers.py:351-352`, `app/serializers.py:367-368`, `app/serializers.py:385-388`, `app/serializers.py:400-401`, `app/serializers.py:417-418`).
  - 실제 response payload test도 `original_response_snapshot`과 `corrected_outcome`이 `null`일 수 있음을 잠급니다 (`tests/test_web_app.py:6191-6192`).
- 이로써 response payload correction/reason field nullability family는 닫혔습니다.
  - `docs/ARCHITECTURE.md:161-165`는 이미 같은 truth를 갖고 있었고,
  - 이번 `/work`가 `docs/PRODUCT_SPEC.md:317-322`도 맞췄습니다.
- 같은 response payload section 안의 다음 smallest current-risk reduction은 `PRODUCT_SPEC` identity/trace field nullability drift입니다.
  - `artifact_id`, `artifact_kind`, `source_message_id`는 shipped response model에서 nullable입니다 (`core/agent_loop.py:69`, `core/agent_loop.py:86-87`).
  - serializer도 그대로 `null`을 내보냅니다. `artifact_id` / `artifact_kind`는 `app/serializers.py:36-37`, `source_message_id`는 `app/serializers.py:38-40`과 `app/serializers.py:390-394` 기준입니다.
  - 실제 current paths 중 일부는 이 필드들을 채우지 않습니다. 예를 들어 corrected-save bridge 오류 경로(`core/agent_loop.py:391-395`, `core/agent_loop.py:399-403`)와 OCR/error 경로(`core/agent_loop.py:8775-8794`)는 `AgentResponse`를 artifact/source anchors 없이 반환합니다.
  - `docs/ARCHITECTURE.md:147-149`는 이미 `string | null`로 truthful하지만, `docs/PRODUCT_SPEC.md:297-300`은 아직 object/value-only처럼 읽힙니다.
- 다음 Claude 슬라이스는 `.pipeline/claude_handoff.md`에 `Docs PRODUCT_SPEC response payload identity trace field nullability truth sync`로 고정했습니다.

## 검증
- `sed -n '1,220p' .agents/skills/round-handoff/SKILL.md`
- `sed -n '1,260p' AGENTS.md`
- `sed -n '1,220p' work/README.md`
- `sed -n '1,220p' verify/README.md`
- `sed -n '1,220p' .pipeline/README.md`
- `sed -n '1,240p' work/4/9/2026-04-09-docs-correction-reason-field-nullability-truth-sync.md`
- `sed -n '1,260p' verify/4/9/2026-04-09-docs-snapshot-response-origin-nullable-truth-sync-verification.md`
- `sed -n '1,220p' docs/NEXT_STEPS.md`
- `sed -n '1,220p' docs/MILESTONES.md`
- `sed -n '1,220p' docs/TASK_BACKLOG.md`
- `git status --short`
- `git diff -- docs/PRODUCT_SPEC.md`
- `git diff --check`
- `rg -n '\\boriginal_response_snapshot\\b|\\bcorrected_outcome\\b|\\bapproval_reason_record\\b|\\bcontent_reason_record\\b|\\bsave_content_source\\b' docs/PRODUCT_SPEC.md docs/ARCHITECTURE.md docs/ACCEPTANCE_CRITERIA.md app/serializers.py core/agent_loop.py tests/test_web_app.py tests/test_smoke.py -S`
- `rg -n '\\bartifact_id\\b|\\bartifact_kind\\b|\\bsource_message_id\\b' docs/PRODUCT_SPEC.md docs/ARCHITECTURE.md docs/ACCEPTANCE_CRITERIA.md app/serializers.py core/agent_loop.py tests/test_web_app.py tests/test_smoke.py -S`
- `rg -n 'artifact_id\\s*:\\s*str \\| None|artifact_kind\\s*:\\s*str \\| None|source_message_id\\s*:\\s*str \\| None' core/agent_loop.py -S`
- `nl -ba docs/PRODUCT_SPEC.md | sed -n '292,304p'`
- `nl -ba docs/PRODUCT_SPEC.md | sed -n '317,323p'`
- `nl -ba docs/ARCHITECTURE.md | sed -n '147,151p'`
- `nl -ba docs/ARCHITECTURE.md | sed -n '161,165p'`
- `nl -ba app/serializers.py | sed -n '35,40p'`
- `nl -ba app/serializers.py | sed -n '57,61p'`
- `nl -ba app/serializers.py | sed -n '347,352p'`
- `nl -ba app/serializers.py | sed -n '365,418p'`
- `nl -ba app/serializers.py | sed -n '390,394p'`
- `nl -ba core/agent_loop.py | sed -n '74,92p'`
- `nl -ba core/agent_loop.py | sed -n '388,405p'`
- `nl -ba core/agent_loop.py | sed -n '8774,8794p'`
- `nl -ba tests/test_web_app.py | sed -n '6187,6193p'`
- `sed -n '1,240p' .pipeline/claude_handoff.md`
- `sed -n '1,200p' .pipeline/gemini_request.md`
- `sed -n '1,200p' .pipeline/operator_request.md`
- `ls -1 verify/4/9`

## 남은 리스크
- 이번 라운드는 docs/code truth 대조와 handoff 갱신만 수행했습니다. Python unit test와 Playwright는 재실행하지 않았습니다.
- response payload correction/reason field nullability family는 닫혔지만, `docs/PRODUCT_SPEC.md`의 response payload identity/trace field list는 아직 `artifact_id`, `artifact_kind`, `source_message_id`의 top-level `null` 가능성을 직접 드러내지 않습니다.
- 현재 worktree에는 이 라운드와 무관한 dirty/untracked 파일이 많이 남아 있으므로 다음 슬라이스도 unrelated changes를 건드리지 말아야 합니다.
