## 변경 파일
- `verify/4/8/2026-04-08-docs-product-spec-acceptance-criteria-session-permissions-field-shape-summary-truth-sync-verification.md`
- `.pipeline/claude_handoff.md`

## 사용 skill
- `round-handoff`

## 변경 이유
- 최신 `/work`의 session permissions summary truth sync가 실제 문서 상태와 serializer contract에 맞는지 다시 확인해야 했습니다.
- truthful 판정 뒤 같은 permission-documentation family에서 남은 다음 한 슬라이스를 하나로 고정해야 했습니다.

## 핵심 변경
- 최신 `/work`는 truthful했습니다.
- [docs/PRODUCT_SPEC.md](/home/xpdlqj/code/projectH/docs/PRODUCT_SPEC.md#L114)는 실제로 `permissions ({web_search, web_search_label})`로 바뀌어 있었고, [docs/ACCEPTANCE_CRITERIA.md](/home/xpdlqj/code/projectH/docs/ACCEPTANCE_CRITERIA.md#L88)도 `permissions — {web_search, web_search_label}`로 반영되어 있었습니다.
- 현재 serializer contract인 [app/serializers.py](/home/xpdlqj/code/projectH/app/serializers.py#L964)~[app/serializers.py](/home/xpdlqj/code/projectH/app/serializers.py#L970), detailed spec line [docs/PRODUCT_SPEC.md](/home/xpdlqj/code/projectH/docs/PRODUCT_SPEC.md#L219), architecture line [docs/ARCHITECTURE.md](/home/xpdlqj/code/projectH/docs/ARCHITECTURE.md#L143)와도 충돌이 없었습니다.
- 다음 Claude 슬라이스는 `.pipeline/claude_handoff.md`에 `Docs ACCEPTANCE_CRITERIA session permissions enum-and-label value-set truth sync`로 고정했습니다.
- 같은 family의 남은 가장 작은 drift는 authoritative acceptance layer가 아직 `permissions`의 shape만 적고, 실제 shipped `web_search` enum 값과 `web_search_label` value set은 적지 않는 점입니다.

## 검증
- `git diff -- docs/PRODUCT_SPEC.md docs/ACCEPTANCE_CRITERIA.md`
- `nl -ba docs/PRODUCT_SPEC.md | sed -n '112,116p'`
- `nl -ba docs/ACCEPTANCE_CRITERIA.md | sed -n '82,90p'`
- `rg -n 'permissions|web_search_label|web-search permission state|\\{web_search, web_search_label\\}' docs/PRODUCT_SPEC.md docs/ACCEPTANCE_CRITERIA.md docs/ARCHITECTURE.md README.md docs/project-brief.md docs/PRODUCT_PROPOSAL.md docs/NEXT_STEPS.md docs/MILESTONES.md docs/TASK_BACKLOG.md -S`
- `rg -n 'web_search_label|permissions\\.web_search|disabled|approval|enabled|차단 · 읽기 전용 검색|승인 필요 · 읽기 전용 검색|허용 · 읽기 전용 검색' docs/ACCEPTANCE_CRITERIA.md docs/PRODUCT_SPEC.md docs/ARCHITECTURE.md -S`
- `nl -ba docs/ACCEPTANCE_CRITERIA.md | sed -n '82,110p'`
- `nl -ba app/serializers.py | sed -n '964,970p'`
- `git diff --check`

## 남은 리스크
- authoritative summary shape drift는 닫혔지만, [docs/ACCEPTANCE_CRITERIA.md](/home/xpdlqj/code/projectH/docs/ACCEPTANCE_CRITERIA.md#L88)는 아직 `permissions`의 exact enum/value set을 적지 않아 acceptance-layer contract detail이 `PRODUCT_SPEC` / `ARCHITECTURE`보다 한 단계 얕습니다.
- 작업 트리에 unrelated dirty files가 남아 있으므로, 다음 슬라이스에서도 해당 파일들은 건드리지 않고 permission docs family만 좁게 수정해야 합니다.
