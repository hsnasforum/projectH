# Docs test-suite label truth sync verification

## 변경 파일
- `verify/4/9/2026-04-09-docs-test-suite-label-truth-sync-verification.md`
- `.pipeline/claude_handoff.md`

## 사용 skill
- `round-handoff`

## 변경 이유
- 최신 `/work` `work/4/9/2026-04-09-docs-test-suite-label-truth-sync.md`가 직전 verification note가 고정한 response payload test-suite labeling drift를 실제로 닫았는지 다시 확인하고, 같은 docs family 안에서 남은 다음 단일 truth-sync 슬라이스를 좁힐 필요가 있었습니다.
- 같은 날짜의 기존 verification note `verify/4/9/2026-04-09-docs-correction-field-test-lock-truth-sync-verification.md`를 먼저 읽은 뒤, 그 다음 `/work`가 실제 handoff scope를 끝까지 닫았는지 재검수했습니다.

## 핵심 변경
- 최신 `/work`는 truthful합니다.
  - `docs/ARCHITECTURE.md:167`은 이제 `tests/test_web_app.py`를 focused service tests, `tests/test_smoke.py`를 Python smoke tests, `e2e/tests/web-smoke.spec.mjs`를 Playwright browser smoke로 정확히 구분합니다.
  - `docs/ACCEPTANCE_CRITERIA.md:121`도 같은 구분을 그대로 반영합니다.
  - 두 문서는 correction/save field anchors (`original_response_snapshot`, `corrected_outcome`, `save_content_source`, `approval_reason_record`, `content_reason_record`)를 같은 tests가 잠근다는 설명도 유지하고 있어, 직전 verification note가 잡았던 오표기 drift를 닫았습니다.
- 실제 tree도 이 문구와 맞습니다.
  - `tests/test_smoke.py:1`부터 Python `unittest` smoke/service suite입니다.
  - 브라우저 smoke는 `e2e/tests/web-smoke.spec.mjs`에 따로 있습니다.
- 다음 Claude 슬라이스는 `.pipeline/claude_handoff.md`에 `Docs PRODUCT_SPEC response payload test-lock suite split truth sync`로 고정했습니다.
  - `docs/PRODUCT_SPEC.md:287`은 아직 `drive shell behavior and test assertions`라고만 적어 service tests / Python smoke tests / Playwright browser smoke의 분리와 correction/save field anchor coverage를 직접 적지 않습니다.
  - 같은 root docs family에서 `ARCHITECTURE`와 `ACCEPTANCE_CRITERIA`는 이미 이 split을 명시하므로, 남은 가장 작은 same-family truth-sync 조각은 `PRODUCT_SPEC` 정렬입니다.

## 검증
- `sed -n '1,240p' work/4/9/2026-04-09-docs-test-suite-label-truth-sync.md`
- `sed -n '1,240p' verify/4/9/2026-04-09-docs-correction-field-test-lock-truth-sync-verification.md`
- `nl -ba docs/ARCHITECTURE.md | sed -n '164,170p'`
- `nl -ba docs/ACCEPTANCE_CRITERIA.md | sed -n '118,124p'`
- `git diff -- docs/ARCHITECTURE.md docs/ACCEPTANCE_CRITERIA.md`
- `rg -n "browser smoke|Python smoke tests|Playwright browser smoke|tests/test_smoke.py|web-smoke.spec.mjs|response payload" docs/PRODUCT_SPEC.md docs/ARCHITECTURE.md docs/ACCEPTANCE_CRITERIA.md README.md docs/MILESTONES.md docs/TASK_BACKLOG.md tests/test_smoke.py tests/test_web_app.py e2e/tests/web-smoke.spec.mjs -S`
- `git diff --check`
- `nl -ba docs/PRODUCT_SPEC.md | sed -n '285,335p'`
- `nl -ba docs/ARCHITECTURE.md | sed -n '320,335p'`
- `rg -n "control fields|correction/save field anchors|top-level response payload|_serialize_response|tests/test_smoke.py|test_web_app.py" docs/PRODUCT_SPEC.md docs/ARCHITECTURE.md docs/ACCEPTANCE_CRITERIA.md -S`
- `sed -n '307,323p' docs/PRODUCT_SPEC.md`
- `sed -n '1,220p' .pipeline/claude_handoff.md`

## 남은 리스크
- 이번 라운드는 docs/code truth 대조와 `git diff --check`만 다시 확인했습니다. Python unit test와 Playwright는 재실행하지 않았습니다.
- `docs/PRODUCT_SPEC.md:287`은 여전히 generic한 `test assertions` wording만 남아 있어, response payload test-lock suite split을 root docs 셋 전체에서 같은 해상도로 맞추려면 한 번 더 정리하는 것이 좋습니다.
