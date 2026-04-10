## 변경 파일
- `verify/4/8/2026-04-08-docs-acceptance-criteria-session-permissions-enum-and-label-value-set-truth-sync-verification.md`
- `.pipeline/claude_handoff.md`

## 사용 skill
- `round-handoff`

## 변경 이유
- 최신 `/work`의 `ACCEPTANCE_CRITERIA` permission enum/value-set truth sync가 실제 문서와 계약에 맞는지 다시 확인해야 했습니다.
- truthful 판정 이후 같은 permission-documentation family에서 남은 다음 한 슬라이스를 고정해야 했습니다.

## 핵심 변경
- 최신 `/work`의 실제 수정은 맞았습니다.
- [docs/ACCEPTANCE_CRITERIA.md](/home/xpdlqj/code/projectH/docs/ACCEPTANCE_CRITERIA.md#L88)는 실제로 `permissions` shape 뒤에 `web_search` enum 값과 `web_search_label` value set까지 포함하도록 갱신되어 있었고, [docs/PRODUCT_SPEC.md](/home/xpdlqj/code/projectH/docs/PRODUCT_SPEC.md#L219), [docs/ARCHITECTURE.md](/home/xpdlqj/code/projectH/docs/ARCHITECTURE.md#L143), [app/serializers.py](/home/xpdlqj/code/projectH/app/serializers.py#L964)~[app/serializers.py](/home/xpdlqj/code/projectH/app/serializers.py#L970)와도 일치했습니다.
- 다만 `/work`의 `남은 리스크 - 없음. permissions 열거값 문서화가 authoritative docs 전체에서 완전 parity 달성.`은 과했습니다.
- 같은 permission docs family 안에 [docs/ARCHITECTURE.md](/home/xpdlqj/code/projectH/docs/ARCHITECTURE.md#L74) `Current implementation note`가 아직 `session_store` persisted fields를 `feedback`, `pending_approvals`, `active_context`까지만 적고 `permissions`를 빠뜨리고 있습니다.
- 실제 구현은 [storage/session_store.py](/home/xpdlqj/code/projectH/storage/session_store.py#L752)~[storage/session_store.py](/home/xpdlqj/code/projectH/storage/session_store.py#L779)에서 normalization 단계에 `permissions`를 포함하고, [storage/session_store.py](/home/xpdlqj/code/projectH/storage/session_store.py#L1419)~[storage/session_store.py](/home/xpdlqj/code/projectH/storage/session_store.py#L1438)에서 `set_permissions` / `get_permissions`도 직접 제공합니다.
- 다음 Claude 슬라이스는 `.pipeline/claude_handoff.md`에 `Docs ARCHITECTURE session_store permissions persistence truth sync`로 고정했습니다.

## 검증
- `git diff -- docs/ACCEPTANCE_CRITERIA.md`
- `nl -ba docs/ACCEPTANCE_CRITERIA.md | sed -n '82,90p'`
- `rg -n 'permissions|web_search_label|disabled|approval|enabled|차단 · 읽기 전용 검색|승인 필요 · 읽기 전용 검색|허용 · 읽기 전용 검색' docs/ACCEPTANCE_CRITERIA.md docs/PRODUCT_SPEC.md docs/ARCHITECTURE.md -S`
- `rg -n 'pending_approvals and active_context|pending_approvals|active_context|permissions' docs/ARCHITECTURE.md storage tests/test_session_store.py app/serializers.py -S`
- `nl -ba docs/ARCHITECTURE.md | sed -n '72,76p'`
- `nl -ba storage/session_store.py | sed -n '752,780p'`
- `nl -ba storage/session_store.py | sed -n '1419,1438p'`
- `git diff --check`

## 남은 리스크
- acceptance-layer enum/value-set drift는 닫혔지만, 같은 family의 [docs/ARCHITECTURE.md](/home/xpdlqj/code/projectH/docs/ARCHITECTURE.md#L74) current-implementation summary가 아직 `permissions` persistence를 빠뜨려 authoritative architecture note가 코드보다 한 단계 덜 truthful합니다.
- 작업 트리에 unrelated dirty files가 남아 있으므로, 다음 슬라이스에서도 해당 파일들은 건드리지 않고 permission docs family만 좁게 수정해야 합니다.
