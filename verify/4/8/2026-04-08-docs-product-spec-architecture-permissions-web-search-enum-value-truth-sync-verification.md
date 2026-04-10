## 변경 파일
- `verify/4/8/2026-04-08-docs-product-spec-architecture-permissions-web-search-enum-value-truth-sync-verification.md`
- `.pipeline/claude_handoff.md`

## 사용 skill
- `round-handoff`

## 변경 이유
- 최신 `/work`의 `permissions.web_search` enum-value truth sync가 실제 구현과 테스트에 맞는지 다시 확인해야 했습니다.
- truthful 판정 이후 같은 family의 다음 최소 문서 truth-sync 슬라이스를 하나로 고정해야 했습니다.

## 핵심 변경
- 최신 `/work`는 truthful하다고 확인했습니다.
- `docs/PRODUCT_SPEC.md:219`와 `docs/ARCHITECTURE.md:143`의 `permissions.web_search`가 실제 shipped enum인 `disabled` / `approval` / `enabled`와 일치했습니다.
- 근거는 `core/contracts.py:149-152`, `app/serializers.py:964-970`, `tests/test_web_app.py:5125-5126`, `tests/test_session_store.py:31-36`에서 다시 대조했습니다.
- 다음 Claude 슬라이스는 `.pipeline/claude_handoff.md`에 `Docs PRODUCT_SPEC ARCHITECTURE permissions web_search_label value truth sync`로 고정했습니다.
- 현재 authoritative docs는 `permissions`가 `{web_search, web_search_label}`임을 적고 있지만, 실제 `web_search_label` 값인 `차단 · 읽기 전용 검색` / `승인 필요 · 읽기 전용 검색` / `허용 · 읽기 전용 검색`까지는 아직 명시하지 않습니다.

## 검증
- `git diff -- docs/PRODUCT_SPEC.md docs/ARCHITECTURE.md`
- `nl -ba docs/PRODUCT_SPEC.md | sed -n '213,220p'`
- `nl -ba docs/ARCHITECTURE.md | sed -n '138,144p'`
- `nl -ba core/contracts.py | sed -n '149,152p'`
- `nl -ba app/web.py | sed -n '188,206p'`
- `rg -n "web_search_label|승인 필요 · 읽기 전용 검색|허용 · 읽기 전용 검색|차단 · 읽기 전용 검색" docs/PRODUCT_SPEC.md docs/ARCHITECTURE.md tests/test_web_app.py app/serializers.py -S`
- `git diff --check`

## 남은 리스크
- `docs/PRODUCT_SPEC.md`와 `docs/ARCHITECTURE.md`는 아직 `permissions.web_search_label`의 exact value set을 authoritative하게 적지 않아 session-schema truth가 한 단계 덜 닫혀 있습니다.
- 작업 트리에 unrelated dirty files가 남아 있으므로, 다음 슬라이스에서도 해당 파일들은 건드리지 않고 현재 문서 family만 좁게 수정해야 합니다.
