## 변경 파일
- `verify/4/8/2026-04-08-docs-product-spec-architecture-pending-approvals-permissions-field-shape-truth-sync-verification.md`
- `.pipeline/claude_handoff.md`

## 사용 skill
- `round-handoff`

## 변경 이유
- 최신 `/work`인 `work/4/8/2026-04-08-docs-product-spec-architecture-pending-approvals-permissions-field-shape-truth-sync.md`가 실제 serializer/test contract 기준으로 truthful한지 다시 확인해야 했습니다.
- 검증 결과를 영속 `/verify`에 남기고, 같은 session-schema family에서 남은 다음 정확한 문서 truth-sync 슬라이스를 Claude에 넘겨야 했습니다.

## 핵심 변경
- 최신 `/work`는 구현과 rerun 자체는 맞았지만, 완전히 truthful하지는 않았습니다.
  - `pending_approvals` 문서화 자체는 맞았습니다. `docs/PRODUCT_SPEC.md:218`과 `docs/ARCHITECTURE.md:142`는 실제 `app/serializers.py:251-253`의 serialized approval object list 직렬화와 맞고, `tests/test_web_app.py:6126-6143`, `tests/test_web_app.py:6407-6416`, `tests/test_smoke.py:2741-2745`도 그 contract를 뒷받침합니다.
  - 다만 `permissions` 문구는 사실과 달랐습니다. `docs/PRODUCT_SPEC.md:219`와 `docs/ARCHITECTURE.md:143`은 `web_search` 값을 `enabled` / `disabled` / `ask`로 적고 있지만, 실제 enum은 `core/contracts.py:149-152`에서 `disabled` / `approval` / `enabled`이고, serializer와 테스트도 `approval`을 사용합니다 (`app/serializers.py:964-970`, `tests/test_web_app.py:5125-5126`, `tests/test_session_store.py:31-36`).
- 다음 Claude 슬라이스를 `.pipeline/claude_handoff.md`에 `Docs PRODUCT_SPEC ARCHITECTURE permissions web_search enum-value truth sync`로 고정했습니다.
  - 현재 남은 가장 작은 same-family current-risk는 authoritative schema docs의 `permissions.web_search` enum drift를 실제 shipped value인 `approval` 기준으로 바로잡는 일입니다.
  - `pending_approvals`는 이미 맞았으므로, 이번에는 `permissions` enum terminology만 좁게 정리하는 편이 가장 정확합니다.

## 검증
- `git diff -- docs/PRODUCT_SPEC.md docs/ARCHITECTURE.md`
- `git diff --check`
- `rg -n "WebSearchPermission|web_search_label|approval\\\"\\)|\\\"approval\\\"|enabled|disabled|ask" app core docs tests -S`
- `git status --short`
- `nl -ba docs/PRODUCT_SPEC.md | sed -n '213,221p'`
- `nl -ba docs/ARCHITECTURE.md | sed -n '138,145p'`
- `nl -ba core/contracts.py | sed -n '149,153p'`
- `nl -ba app/serializers.py | sed -n '964,970p'`
- `nl -ba tests/test_web_app.py | sed -n '5124,5126p'`
- `nl -ba tests/test_session_store.py | sed -n '29,36p'`

## 남은 리스크
- `docs/PRODUCT_SPEC.md`와 `docs/ARCHITECTURE.md`의 `permissions.web_search` enum wording은 아직 구현과 맞지 않아, authoritative session-schema layer에 직접적인 terminology drift가 남아 있습니다.
- 작업 트리에는 `.gitignore`, `.pipeline/README.md`, `AGENTS.md`, `CLAUDE.md`, `GEMINI.md`, `PROJECT_CUSTOM_INSTRUCTIONS.md`, `pipeline_gui/*`, `watcher_core.py`, 관련 테스트와 문서 등 이번 슬라이스와 무관한 변경이 이미 있으므로 건드리지 않았습니다.
