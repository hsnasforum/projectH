## 변경 파일
- `verify/4/8/2026-04-08-docs-product-spec-architecture-evidence-summary-chunks-field-shape-truth-sync-verification.md`
- `.pipeline/claude_handoff.md`

## 사용 skill
- `round-handoff`

## 변경 이유
- 최신 `/work`인 `work/4/8/2026-04-08-docs-product-spec-architecture-evidence-summary-chunks-field-shape-truth-sync.md`가 실제 serializer/test contract 기준으로 truthful한지 다시 확인해야 했습니다.
- 검증 결과를 영속 `/verify`에 남기고, 같은 session/response metadata family에서 남은 다음 정확한 문서 truth-sync 슬라이스를 Claude에 넘겨야 했습니다.

## 핵심 변경
- 최신 `/work`는 truthful했습니다.
  - `docs/PRODUCT_SPEC.md:254-255`, `docs/ARCHITECTURE.md:168-169`, `docs/PRODUCT_SPEC.md:415-416`, `docs/PRODUCT_SPEC.md:480-481`, `docs/ARCHITECTURE.md:300-301`이 실제 shipped `evidence`, `summary_chunks`, `evidence_snapshot`, `summary_chunks_snapshot` shape를 문서화하고 있음을 확인했습니다.
  - 문서의 field 목록은 `app/serializers.py:895-934`가 실제로 직렬화하는 `evidence.{label, source_name, source_path, snippet, source_role}` 및 `summary_chunks.{chunk_id, chunk_index, total_chunks, source_path, source_name, selected_line}`와 맞고, `app/serializers.py:353-360`의 snapshot 직렬화도 그 same shape를 재사용합니다.
  - `tests/test_web_app.py:4492-4501`, `tests/test_web_app.py:5953-5956`, `tests/test_smoke.py:3583-3584`, `tests/test_smoke.py:3628-3630`, `tests/test_smoke.py:2725-2732`도 핵심 contract를 이미 검증하고 있어 `/work`의 설명과 충돌하지 않았습니다.
- 다음 Claude 슬라이스를 `.pipeline/claude_handoff.md`에 `Docs PRODUCT_SPEC ARCHITECTURE pending_approvals permissions field-shape truth sync`로 고정했습니다.
  - `docs/PRODUCT_SPEC.md:218-219`와 `docs/ARCHITECTURE.md:142-143`는 아직 `pending_approvals`와 `permissions`를 이름 수준으로만 적고 있습니다.
  - 실제 shipped serializer는 `app/serializers.py:251-257`에서 `pending_approvals`를 current approval object list로, `permissions`를 `{web_search, web_search_label}` shape로 직렬화합니다.
  - 관련 contract는 `tests/test_web_app.py:6126-6143`, `tests/test_web_app.py:6407-6416`, `tests/test_web_app.py:5124-5126`, `tests/test_smoke.py:2741-2745`, `tests/test_smoke.py:2925-2935`, `tests/test_smoke.py:7726-7727`에서도 이미 확인되고 있어, 같은 family의 다음 current-risk reduction으로 적절합니다.

## 검증
- `git diff -- docs/PRODUCT_SPEC.md docs/ARCHITECTURE.md`
- `git diff --check`
- `rg -n -F 'list of `{label, source_name, source_path, snippet, source_role}`' docs/PRODUCT_SPEC.md docs/ARCHITECTURE.md`
- `rg -n -F 'list of `{chunk_id, chunk_index, total_chunks, source_path, source_name, selected_line}`' docs/PRODUCT_SPEC.md docs/ARCHITECTURE.md`
- `rg -n -F 'same shape as message-level \`summary_chunks\`' docs/PRODUCT_SPEC.md docs/ARCHITECTURE.md`
- `rg -n -F 'same shape as message-level \`evidence\`' docs/PRODUCT_SPEC.md docs/ARCHITECTURE.md`
- `rg -n "feedback|content_reason_record|approval_reason_record|approval metadata|pending_approvals|permissions" docs/PRODUCT_SPEC.md docs/ARCHITECTURE.md app/serializers.py tests/test_web_app.py tests/test_smoke.py -S`
- `git status --short`

## 남은 리스크
- `docs/PRODUCT_SPEC.md`와 `docs/ARCHITECTURE.md`는 아직 session-level `pending_approvals` / `permissions` exact shape를 fully document하지 않아, session schema truth drift가 남아 있습니다.
- 작업 트리에는 `.gitignore`, `.pipeline/README.md`, `AGENTS.md`, `CLAUDE.md`, `GEMINI.md`, `PROJECT_CUSTOM_INSTRUCTIONS.md`, `pipeline_gui/*`, `watcher_core.py`, 관련 테스트와 문서 등 이번 슬라이스와 무관한 변경이 이미 있으므로 건드리지 않았습니다.
