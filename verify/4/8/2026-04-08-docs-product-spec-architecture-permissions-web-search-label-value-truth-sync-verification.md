## 변경 파일
- `verify/4/8/2026-04-08-docs-product-spec-architecture-permissions-web-search-label-value-truth-sync-verification.md`
- `.pipeline/claude_handoff.md`

## 사용 skill
- `round-handoff`

## 변경 이유
- 최신 `/work`의 `permissions.web_search_label` value truth sync가 실제 구현과 문서에 맞는지 다시 확인해야 했습니다.
- truthful 판정 뒤 같은 session-schema family에서 남은 다음 한 슬라이스를 고정해야 했습니다.

## 핵심 변경
- 최신 `/work`는 구현과 rerun 자체는 맞았지만, 완전히 truthful하지는 않았습니다.
- [docs/PRODUCT_SPEC.md](/home/xpdlqj/code/projectH/docs/PRODUCT_SPEC.md#L219)와 [docs/ARCHITECTURE.md](/home/xpdlqj/code/projectH/docs/ARCHITECTURE.md#L143)의 `permissions.web_search_label` 값 세트는 실제 shipped 구현과 일치했습니다.
- 근거는 [app/web.py](/home/xpdlqj/code/projectH/app/web.py#L193)~[app/web.py](/home/xpdlqj/code/projectH/app/web.py#L199), [app/serializers.py](/home/xpdlqj/code/projectH/app/serializers.py#L964)~[app/serializers.py](/home/xpdlqj/code/projectH/app/serializers.py#L970), [tests/test_web_app.py](/home/xpdlqj/code/projectH/tests/test_web_app.py#L5125)~[tests/test_web_app.py](/home/xpdlqj/code/projectH/tests/test_web_app.py#L5126)에서 다시 대조했습니다.
- 다만 `/work`의 `남은 리스크 - 없음`은 과했습니다. 같은 family의 high-level docs에 아직 `enabled/disabled/ask per session` wording이 남아 있습니다.
- 현재 남은 stale wording은 [docs/PRODUCT_SPEC.md](/home/xpdlqj/code/projectH/docs/PRODUCT_SPEC.md#L111), [docs/PRODUCT_SPEC.md](/home/xpdlqj/code/projectH/docs/PRODUCT_SPEC.md#L152), [docs/PRODUCT_SPEC.md](/home/xpdlqj/code/projectH/docs/PRODUCT_SPEC.md#L306), [docs/project-brief.md](/home/xpdlqj/code/projectH/docs/project-brief.md#L15), [docs/project-brief.md](/home/xpdlqj/code/projectH/docs/project-brief.md#L79), [docs/PRODUCT_PROPOSAL.md](/home/xpdlqj/code/projectH/docs/PRODUCT_PROPOSAL.md#L26), [docs/PRODUCT_PROPOSAL.md](/home/xpdlqj/code/projectH/docs/PRODUCT_PROPOSAL.md#L59), [docs/PRODUCT_PROPOSAL.md](/home/xpdlqj/code/projectH/docs/PRODUCT_PROPOSAL.md#L65), [docs/NEXT_STEPS.md](/home/xpdlqj/code/projectH/docs/NEXT_STEPS.md#L15), [docs/MILESTONES.md](/home/xpdlqj/code/projectH/docs/MILESTONES.md#L7), [docs/TASK_BACKLOG.md](/home/xpdlqj/code/projectH/docs/TASK_BACKLOG.md#L7)입니다.
- 다음 Claude 슬라이스는 `.pipeline/claude_handoff.md`에 `Docs PRODUCT_SPEC project-brief PRODUCT_PROPOSAL NEXT_STEPS MILESTONES TASK_BACKLOG web-search permission-mode wording truth sync`로 고정했습니다.

## 검증
- `git diff -- docs/PRODUCT_SPEC.md docs/ARCHITECTURE.md`
- `nl -ba docs/PRODUCT_SPEC.md | sed -n '216,221p'`
- `nl -ba docs/ARCHITECTURE.md | sed -n '140,145p'`
- `nl -ba app/web.py | sed -n '193,199p'`
- `nl -ba app/serializers.py | sed -n '964,970p'`
- `nl -ba tests/test_web_app.py | sed -n '5123,5128p'`
- `rg -n 'enabled/disabled/ask per session|enabled / disabled / ask|\\bask per session\\b|permission-gated web investigation \\(enabled/disabled/ask' README.md docs plandoc AGENTS.md CLAUDE.md GEMINI.md PROJECT_CUSTOM_INSTRUCTIONS.md -S`
- `rg -n 'web-search permission gate|permission state|web_search_label|web_search' docs/PRODUCT_SPEC.md docs/ARCHITECTURE.md docs/ACCEPTANCE_CRITERIA.md README.md -S`
- `git diff --check`

## 남은 리스크
- authoritative field-shape 문서는 맞지만, 같은 family의 high-level docs에는 아직 `ask` wording이 남아 있어 current shipped permission contract 설명이 문서 계층 전반에서 완전히 닫히지 않았습니다.
- 작업 트리에 unrelated dirty files가 남아 있으므로, 다음 슬라이스에서도 해당 파일들은 건드리지 않고 남은 docs wording만 좁게 정리해야 합니다.
