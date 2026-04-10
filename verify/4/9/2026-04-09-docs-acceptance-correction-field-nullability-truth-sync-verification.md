# Docs acceptance correction field nullability truth sync verification

## 변경 파일
- `verify/4/9/2026-04-09-docs-acceptance-correction-field-nullability-truth-sync-verification.md`
- `.pipeline/claude_handoff.md`

## 사용 skill
- `round-handoff`

## 변경 이유
- 최신 `/work` `work/4/9/2026-04-09-docs-acceptance-correction-field-nullability-truth-sync.md`가 직전 verification note가 고정한 `ACCEPTANCE_CRITERIA` response payload correction field drift를 실제로 닫았는지 다시 확인하고, 같은 docs family의 다음 단일 current-risk reduction 슬라이스를 좁힐 필요가 있었습니다.
- 같은 날짜의 기존 verification note `verify/4/9/2026-04-09-docs-arch-acceptance-control-content-field-truth-sync-verification.md`를 먼저 읽은 뒤, 그 후속 `/work`가 실제 handoff scope를 끝까지 닫았는지 재검수했습니다.

## 핵심 변경
- 최신 `/work`는 부분적으로 truthful합니다.
  - `docs/ACCEPTANCE_CRITERIA.md:120`은 이제 `original_response_snapshot`, `corrected_outcome`, `approval_reason_record`, `content_reason_record`, `save_content_source`를 모두 `(nullable)`로 적고 `all null when absent`를 명시합니다.
  - 이 nullability 자체는 shipped serializer/model truth와 맞습니다. top-level response payload는 해당 correction fields를 항상 포함하되 값이 없으면 `null`을 직렬화합니다 (`app/serializers.py:57-61`, `app/serializers.py:347-418`, `core/agent_loop.py:88-92`).
- 하지만 이번 `/work` closeout이 주장한 “response payload 계약 전체 family 완료”는 아직 과합니다.
  - 직전 handoff scope는 nullable뿐 아니라 top-level response payload의 `save_content_source` value semantics도 `docs/PRODUCT_SPEC.md` / `docs/ARCHITECTURE.md`와 맞추도록 요구했습니다.
  - 현재 `docs/ACCEPTANCE_CRITERIA.md:120`은 `save_content_source`를 `(nullable)`로만 적고 있어, top-level response payload에서 허용되는 shipped 값 `original_draft | corrected_text | null`을 직접 닫지 못합니다.
  - canonical docs는 이미 그 truth를 적고 있습니다 (`docs/PRODUCT_SPEC.md:322`, `docs/ARCHITECTURE.md:165`).
  - 구현과 테스트도 현재 shipped 값 축을 그 두 값으로 잠급니다 (`core/approval.py:17-18`, `app/serializers.py:61`, `app/serializers.py:384-388`, `tests/test_web_app.py:721`, `tests/test_web_app.py:6187`, `tests/test_smoke.py:4789`, `tests/test_smoke.py:4410`).
- 따라서 최신 `/work`는 correction-field nullability drift는 닫았지만, `ACCEPTANCE_CRITERIA` top-level response payload correction-field family를 완전히 닫았다고 보기는 어렵습니다.
- 다음 Claude 슬라이스는 `.pipeline/claude_handoff.md`에 `Docs ACCEPTANCE_CRITERIA response payload save_content_source enum truth sync`로 고정했습니다.

## 검증
- `sed -n '1,240p' .agents/skills/round-handoff/SKILL.md`
- `sed -n '1,260p' AGENTS.md`
- `sed -n '1,220p' work/README.md`
- `sed -n '1,220p' verify/README.md`
- `sed -n '1,220p' .pipeline/README.md`
- `sed -n '1,240p' work/4/9/2026-04-09-docs-acceptance-correction-field-nullability-truth-sync.md`
- `sed -n '1,240p' verify/4/9/2026-04-09-docs-arch-acceptance-control-content-field-truth-sync-verification.md`
- `sed -n '1,220p' docs/NEXT_STEPS.md`
- `sed -n '1,220p' docs/MILESTONES.md`
- `sed -n '1,220p' docs/TASK_BACKLOG.md`
- `git status --short`
- `git diff -- docs/ACCEPTANCE_CRITERIA.md`
- `git diff --check`
- `nl -ba docs/ACCEPTANCE_CRITERIA.md | sed -n '114,122p'`
- `nl -ba docs/PRODUCT_SPEC.md | sed -n '289,323p'`
- `nl -ba docs/ARCHITECTURE.md | sed -n '139,165p'`
- `nl -ba core/agent_loop.py | sed -n '69,94p'`
- `nl -ba app/serializers.py | sed -n '35,73p'`
- `nl -ba app/serializers.py | sed -n '347,418p'`
- `nl -ba tests/test_web_app.py | sed -n '6187,6193p'`
- `sed -n '1,240p' .pipeline/claude_handoff.md`
- `rg -n 'save_content_source' docs/ACCEPTANCE_CRITERIA.md docs/PRODUCT_SPEC.md docs/ARCHITECTURE.md tests/test_web_app.py tests/test_smoke.py core/agent_loop.py app/serializers.py -S`
- `nl -ba docs/ACCEPTANCE_CRITERIA.md | sed -n '108,122p'`
- `rg -n 'assertEqual\\([^\\n]*save_content_source|save_content_source\\], \"original_draft\"|save_content_source\\], \"corrected_text\"' tests/test_web_app.py tests/test_smoke.py -S`
- `rg -n 'SAVE_CONTENT_SOURCE_ORIGINAL_DRAFT|SAVE_CONTENT_SOURCE_CORRECTED_TEXT' core -S`
- `ls -1 verify/4/9`
- `sed -n '1,220p' .pipeline/gemini_request.md`
- `sed -n '1,220p' .pipeline/operator_request.md`

## 남은 리스크
- 이번 라운드는 docs/code truth 대조와 handoff 갱신만 수행했습니다. Python unit test와 Playwright는 재실행하지 않았습니다.
- `docs/ACCEPTANCE_CRITERIA.md:120`은 correction-field nullability는 맞췄지만, top-level response payload `save_content_source`의 shipped enum `original_draft | corrected_text | null`은 아직 직접 잠그지 못합니다.
- 현재 worktree에는 이 라운드와 무관한 dirty/untracked 파일이 많이 남아 있으므로 다음 슬라이스도 unrelated changes를 건드리지 말아야 합니다.
