## 변경 파일
- `verify/4/8/2026-04-08-docs-product-spec-architecture-original-response-snapshot-response-origin-nested-field-shape-truth-sync-verification.md`
- `.pipeline/claude_handoff.md`

## 사용 skill
- `round-handoff`

## 변경 이유
- 최신 `/work`인 `work/4/8/2026-04-08-docs-product-spec-architecture-original-response-snapshot-response-origin-nested-field-shape-truth-sync.md`가 실제 serializer/test contract 기준으로 truthful한지 다시 확인해야 했습니다.
- 검증 결과를 영속 `/verify`에 남기고, 같은 response metadata family에서 남은 다음 정확한 문서 truth-sync 슬라이스를 Claude에 넘겨야 했습니다.

## 핵심 변경
- 최신 `/work`는 truthful했습니다.
  - `docs/PRODUCT_SPEC.md:414`, `docs/PRODUCT_SPEC.md:479`, `docs/ARCHITECTURE.md:299`가 실제 shipped `original_response_snapshot.response_origin` nested shape를 문서화하고 있음을 확인했습니다.
  - 문서의 field 목록은 `app/serializers.py:353-360`이 `original_response_snapshot`을 직렬화하면서 `app/serializers.py:337-344`의 message-level `response_origin` shape를 그대로 재사용하는 구현과 맞습니다.
  - `tests/test_web_app.py:4498-4501`, `tests/test_web_app.py:4517-4522`, `tests/test_web_app.py:4576-4582`, `tests/test_smoke.py:2725-2731`도 nested snapshot contract를 이미 검증하고 있어 `/work`의 설명과 충돌하지 않았습니다.
- 다음 Claude 슬라이스를 `.pipeline/claude_handoff.md`에 `Docs PRODUCT_SPEC ARCHITECTURE evidence summary_chunks field-shape truth sync`로 고정했습니다.
  - `docs/PRODUCT_SPEC.md:254-255`, `docs/PRODUCT_SPEC.md:415-416`, `docs/PRODUCT_SPEC.md:480-481`, `docs/ARCHITECTURE.md:168-169`, `docs/ARCHITECTURE.md:300-301`은 아직 `evidence`, `summary_chunks`, `evidence_snapshot`, `summary_chunks_snapshot`를 이름 수준으로만 적고 있습니다.
  - 실제 shipped serializer는 `app/serializers.py:895-934`에서 `evidence`를 `{label, source_name, source_path, snippet, source_role}`, `summary_chunks`를 `{chunk_id, chunk_index, total_chunks, source_path, source_name, selected_line}` shape로 직렬화합니다.
  - 관련 contract는 `tests/test_web_app.py:4493`, `tests/test_web_app.py:4500-4501`, `tests/test_web_app.py:5954-5956`, `tests/test_smoke.py:3584`, `tests/test_smoke.py:3628-3630`, `tests/test_smoke.py:2727-2732`에서도 확인되고 있어, 같은 family의 다음 current-risk reduction으로 적절합니다.

## 검증
- `git diff -- docs/PRODUCT_SPEC.md docs/ARCHITECTURE.md`
- `git diff --check`
- `rg -n "response_origin" docs/PRODUCT_SPEC.md docs/ARCHITECTURE.md`
- `rg -n "summary_chunks_snapshot|evidence_snapshot" docs/PRODUCT_SPEC.md docs/ARCHITECTURE.md docs/ACCEPTANCE_CRITERIA.md docs/NEXT_STEPS.md README.md`
- `rg -n "summary_chunks_snapshot|evidence_snapshot" tests/test_web_app.py tests/test_smoke.py app/serializers.py -S`
- `rg -n "selected_line|chunk_id|chunk_index|total_chunks|snippet|source_role|source_name|source_path" docs/PRODUCT_SPEC.md docs/ARCHITECTURE.md README.md docs/ACCEPTANCE_CRITERIA.md -S`
- `rg -n "def _serialize_summary_chunks|def _serialize_evidence" app/serializers.py`
- `git status --short`

## 남은 리스크
- `docs/PRODUCT_SPEC.md`와 `docs/ARCHITECTURE.md`는 아직 `evidence` / `summary_chunks`와 대응하는 `evidence_snapshot` / `summary_chunks_snapshot` exact field-shape를 fully document하지 않아, response metadata truth drift가 남아 있습니다.
- 작업 트리에는 `.gitignore`, `.pipeline/README.md`, `AGENTS.md`, `CLAUDE.md`, `GEMINI.md`, `PROJECT_CUSTOM_INSTRUCTIONS.md`, `pipeline_gui/*`, `watcher_core.py`, 관련 테스트와 문서 등 이번 슬라이스와 무관한 변경이 이미 있으므로 건드리지 않았습니다.
