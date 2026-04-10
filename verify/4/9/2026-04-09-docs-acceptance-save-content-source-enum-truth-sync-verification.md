# Docs acceptance save_content_source enum truth sync verification

## 변경 파일
- `verify/4/9/2026-04-09-docs-acceptance-save-content-source-enum-truth-sync-verification.md`
- `.pipeline/claude_handoff.md`

## 사용 skill
- `round-handoff`

## 변경 이유
- 최신 `/work` `work/4/9/2026-04-09-docs-acceptance-save-content-source-enum-truth-sync.md`가 직전 verification note가 고정한 `ACCEPTANCE_CRITERIA` top-level response payload `save_content_source` enum drift를 실제로 닫았는지 다시 확인하고, 같은 response payload docs family의 다음 단일 current-risk reduction 슬라이스를 좁힐 필요가 있었습니다.
- 같은 날짜의 기존 verification note `verify/4/9/2026-04-09-docs-acceptance-correction-field-nullability-truth-sync-verification.md`를 먼저 읽은 뒤, 그 후속 `/work`가 실제 handoff scope를 끝까지 닫았는지 재검수했습니다.

## 핵심 변경
- 최신 `/work`는 truthful합니다.
  - `docs/ACCEPTANCE_CRITERIA.md:120`은 이제 `save_content_source`를 `` `original_draft` | `corrected_text` | `null` ``로 적어, 같은 line의 correction-field nullability 설명과 함께 top-level response payload value contract를 직접 닫습니다.
  - 이 문구는 canonical docs와 일치합니다 (`docs/PRODUCT_SPEC.md:317-322`, `docs/ARCHITECTURE.md:161-165`).
  - 구현 truth도 같습니다. enum source는 `core/approval.py:17-18`, top-level response serializer는 `app/serializers.py:57-61`과 `app/serializers.py:384-388`, focused tests는 `tests/test_web_app.py:6247-6257`, `tests/test_web_app.py:6187-6192`, `tests/test_smoke.py:4410-4412`, `tests/test_smoke.py:4789-4802`가 잡고 있습니다.
- 따라서 response payload correction-field family의 3개 canonical docs truth sync는 완료됐습니다.
- 같은 response payload docs family 안의 다음 smallest current-risk reduction은 test-lock wording truth sync입니다.
  - `docs/ARCHITECTURE.md:167`은 아직 focused tests와 browser smoke tests가 `control fields`만 잠근다고 적습니다.
  - `docs/ACCEPTANCE_CRITERIA.md:121`도 같은 식으로 `control fields`만 잠근다고 적습니다.
  - 하지만 현재 tests는 control fields뿐 아니라 response payload correction/save fields도 직접 잠급니다:
    - `original_response_snapshot`, `corrected_outcome`, `save_content_source` (`tests/test_web_app.py:6247-6257`, `tests/test_web_app.py:6187-6192`)
    - `content_reason_record` (`tests/test_web_app.py:490-498`, `tests/test_smoke.py:4648-4664`)
    - `approval_reason_record` (`tests/test_web_app.py:6391-6398`, `tests/test_web_app.py:7112-7117`)
- 다음 Claude 슬라이스는 `.pipeline/claude_handoff.md`에 `Docs ARCHITECTURE ACCEPTANCE_CRITERIA response payload correction field test-lock truth sync`로 고정했습니다.

## 검증
- `sed -n '1,240p' .agents/skills/round-handoff/SKILL.md`
- `sed -n '1,260p' AGENTS.md`
- `sed -n '1,220p' work/README.md`
- `sed -n '1,220p' verify/README.md`
- `sed -n '1,220p' .pipeline/README.md`
- `sed -n '1,240p' work/4/9/2026-04-09-docs-acceptance-save-content-source-enum-truth-sync.md`
- `sed -n '1,260p' verify/4/9/2026-04-09-docs-acceptance-correction-field-nullability-truth-sync-verification.md`
- `sed -n '1,220p' docs/NEXT_STEPS.md`
- `sed -n '1,220p' docs/MILESTONES.md`
- `sed -n '1,220p' docs/TASK_BACKLOG.md`
- `git status --short`
- `git diff -- docs/ACCEPTANCE_CRITERIA.md`
- `git diff --check`
- `nl -ba docs/ACCEPTANCE_CRITERIA.md | sed -n '114,122p'`
- `nl -ba docs/PRODUCT_SPEC.md | sed -n '317,323p'`
- `nl -ba docs/ARCHITECTURE.md | sed -n '161,165p'`
- `nl -ba core/approval.py | sed -n '1,60p'`
- `nl -ba app/serializers.py | sed -n '57,61p'`
- `nl -ba app/serializers.py | sed -n '384,388p'`
- `rg -n 'save_content_source\\].*original_draft|save_content_source\\].*corrected_text|save_content_source, "original_draft"|save_content_source, "corrected_text"' tests/test_web_app.py tests/test_smoke.py -S`
- `sed -n '1,240p' .pipeline/claude_handoff.md`
- `rg -n 'Response Payload Contract|control fields|Correction fields|save_content_source|original_response_snapshot|corrected_outcome|approval_reason_record|content_reason_record|actions_taken|search_results|selected_source_paths|response_origin' docs/PRODUCT_SPEC.md docs/ARCHITECTURE.md docs/ACCEPTANCE_CRITERIA.md README.md -S`
- `rg -n 'lock the control fields|locks the control fields|browser smoke tests|Service tests' docs/ACCEPTANCE_CRITERIA.md docs/ARCHITECTURE.md docs/PRODUCT_SPEC.md -S`
- `nl -ba docs/ARCHITECTURE.md | sed -n '166,168p'`
- `rg -n 'original_response_snapshot|corrected_outcome|approval_reason_record|content_reason_record|save_content_source' tests/test_web_app.py tests/test_smoke.py -S`
- `nl -ba tests/test_web_app.py | sed -n '490,498p'`
- `nl -ba tests/test_web_app.py | sed -n '6391,6398p'`
- `nl -ba tests/test_web_app.py | sed -n '7112,7117p'`
- `nl -ba tests/test_web_app.py | sed -n '6247,6257p'`
- `nl -ba tests/test_smoke.py | sed -n '4648,4664p'`
- `ls -1 verify/4/9`
- `ls -1 work/4/9`

## 남은 리스크
- 이번 라운드는 docs/code truth 대조와 handoff 갱신만 수행했습니다. Python unit test와 Playwright는 재실행하지 않았습니다.
- response payload correction-field family 문구는 닫혔지만, `docs/ARCHITECTURE.md:167`과 `docs/ACCEPTANCE_CRITERIA.md:121`의 test-lock wording은 아직 focused tests가 control fields만 잠근다고 읽히며 현재 tree보다 좁습니다.
- 현재 worktree에는 이 라운드와 무관한 dirty/untracked 파일이 많이 남아 있으므로 다음 슬라이스도 unrelated changes를 건드리지 말아야 합니다.
