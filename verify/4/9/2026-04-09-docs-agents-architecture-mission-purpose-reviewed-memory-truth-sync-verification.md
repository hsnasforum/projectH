# docs: AGENTS ARCHITECTURE mission-purpose reviewed-memory truth sync verification

## 변경 파일
- `verify/4/9/2026-04-09-docs-agents-architecture-mission-purpose-reviewed-memory-truth-sync-verification.md`
- `.pipeline/claude_handoff.md`

## 사용 skill
- `round-handoff`

## 변경 이유
- 최신 `/work`가 `AGENTS.md`와 `docs/ARCHITECTURE.md`의 top-level mission / purpose wording을 현재 shipped reviewed-memory truth와 맞췄다고 주장하므로, direct target truth부터 다시 확인해야 했습니다.
- same-day docs-only truth-sync가 길게 이어진 상태라, direct target이 truthful하더라도 같은 family residual이 남으면 그 잔여를 한 번에 닫는 bounded bundle로 넘겨야 했습니다.

## 핵심 변경
- 최신 `/work`의 직접 수정 대상은 truthful합니다.
  - `AGENTS.md:5`
  - `docs/ARCHITECTURE.md:5`
- 위 문구는 현재 shipped reviewed-memory first slice와 맞습니다.
  - `docs/PRODUCT_SPEC.md:58`
  - `docs/PRODUCT_SPEC.md:60`
  - `docs/ARCHITECTURE.md:15`
  - `docs/ARCHITECTURE.md:85`
  - `app/templates/index.html:24`
  - `app/templates/index.html:29`
  - `tests/test_web_app.py:166`
  - `tests/test_web_app.py:170`
  - `tests/test_web_app.py:7300`
- top-level mission / purpose family는 이번 라운드로 닫힌 쪽에 가깝습니다.
- 다만 최신 `/work`의 `남은 리스크 없음`은 repo 전체 reviewed-memory docs family 기준으로는 약간 과합니다.
  - lower-level historical wording residual이 아직 남아 있습니다.
    - `docs/PRODUCT_SPEC.md:415`
    - `docs/PRODUCT_SPEC.md:970`
    - `docs/ACCEPTANCE_CRITERIA.md:186`
  - 이 구간들은 초기 artifact-entry slice 문맥을 설명하면서도 현재 shipped read-only review queue / reviewed-memory first slice를 이미 연 문서 집합과 나란히 읽힐 때는 현 시점 truth를 다소 과하게 닫아 보이게 만듭니다.
- 따라서 latest `/work` 자체는 truthful하지만, repo-level family closure 주장까지는 그대로 받기 어렵습니다.
- 다음 슬라이스는 `docs/PRODUCT_SPEC.md`와 `docs/ACCEPTANCE_CRITERIA.md`를 함께 묶어 reviewed-memory entry-slice historical wording을 현재 shipped truth에 맞추는 bounded bundle이 적절합니다.

## 검증
- `sed -n '1,220p' work/4/9/2026-04-09-docs-agents-architecture-mission-purpose-reviewed-memory-truth-sync.md`
- `sed -n '1,240p' verify/4/9/2026-04-09-docs-top-level-one-line-current-identity-reviewed-memory-truth-sync-verification.md`
- `git diff --check`
- `nl -ba AGENTS.md | sed -n '1,8p'`
- `nl -ba docs/ARCHITECTURE.md | sed -n '1,8p'`
- `git diff -- AGENTS.md docs/ARCHITECTURE.md`
- `rg -n --no-heading 'local-first AI assistant web MVP|first reviewed-memory slice shipped|first reviewed-memory slice \\(|active-effect path|Mission|## Purpose|## Mission' AGENTS.md docs/ARCHITECTURE.md README.md CLAUDE.md PROJECT_CUSTOM_INSTRUCTIONS.md docs/PRODUCT_SPEC.md docs/PRODUCT_PROPOSAL.md docs/project-brief.md docs/TASK_BACKLOG.md docs/MILESTONES.md`
- `rg -n --no-heading 'first reviewed-memory slice|review queue|검토 후보|aggregate apply trigger|active-effect path|reviewed-memory active-effect' README.md CLAUDE.md PROJECT_CUSTOM_INSTRUCTIONS.md docs/PRODUCT_SPEC.md docs/project-brief.md docs/PRODUCT_PROPOSAL.md docs/TASK_BACKLOG.md docs/ARCHITECTURE.md docs/MILESTONES.md docs/NEXT_STEPS.md docs/ACCEPTANCE_CRITERIA.md AGENTS.md app/templates/index.html tests/test_web_app.py`
- `rg -n --no-heading 'no review queue|not review queue or user-level memory|reviewed memory and user-level memory still remain closed|review queue or user-level memory|user-level memory still remain closed|first implementation slice is \`artifact_id\` linkage' docs/PRODUCT_SPEC.md docs/ACCEPTANCE_CRITERIA.md docs/ARCHITECTURE.md docs/TASK_BACKLOG.md docs/NEXT_STEPS.md docs/MILESTONES.md`
- `nl -ba docs/PRODUCT_SPEC.md | sed -n '960,972p'`
- `nl -ba docs/ACCEPTANCE_CRITERIA.md | sed -n '184,187p'`
- `nl -ba docs/PRODUCT_SPEC.md | sed -n '411,416p'`
- Python unit test와 Playwright는 재실행하지 않았습니다. 최신 `/work`가 docs-only이고 code/test/runtime 변경을 주장하지 않았기 때문입니다.

## 남은 리스크
- 최신 `/work`의 직접 수정 대상은 truthful합니다.
- 다만 repo-level reviewed-memory docs truth-sync는 `docs/PRODUCT_SPEC.md:415`, `docs/PRODUCT_SPEC.md:970`, `docs/ACCEPTANCE_CRITERIA.md:186`의 entry-slice historical wording까지는 아직 완전히 닫히지 않았습니다.
