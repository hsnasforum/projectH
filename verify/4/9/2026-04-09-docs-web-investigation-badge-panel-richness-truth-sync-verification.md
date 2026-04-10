# docs: web-investigation badge-and-panel richness truth sync verification

## 변경 파일
- `verify/4/9/2026-04-09-docs-web-investigation-badge-panel-richness-truth-sync-verification.md`
- `.pipeline/claude_handoff.md`

## 사용 skill
- `round-handoff`

## 변경 이유
- 최신 `/work`가 web-investigation current-surface badge shorthand를 실제로 richer shipped wording과 맞췄는지 다시 확인해야 했습니다.
- direct target이 truthful하더라도, `/work`가 주장한 badge-and-panel richness family closure까지 수용할 수 있는지는 별도로 좁게 재대조해야 했습니다.

## 핵심 변경
- 최신 `/work`의 직접 수정 대상은 truthful합니다.
  - `AGENTS.md:45`
  - `CLAUDE.md:24`
  - `PROJECT_CUSTOM_INSTRUCTIONS.md:22`
  - `docs/ARCHITECTURE.md:11`
  - `docs/ARCHITECTURE.md:137`
  - `docs/ARCHITECTURE.md:1372`
  - `docs/PRODUCT_PROPOSAL.md:26`
  - `docs/PRODUCT_PROPOSAL.md:63`
  - `docs/project-brief.md:15`
  - `docs/project-brief.md:87`
  - `docs/NEXT_STEPS.md:21`
  - `docs/TASK_BACKLOG.md:24`
- 위 줄들은 badge richness 기준 shipped truth와 맞습니다.
  - `README.md:78`
  - `docs/PRODUCT_SPEC.md:339`
  - `docs/PRODUCT_SPEC.md:359`
- 다만 latest `/work`의 `남은 리스크 없음`과 `전체 repo docs의 web-investigation badge-and-panel richness 동기화 완료` 주장은 과합니다.
  - same-family badge shorthand residual이 아직 남아 있습니다.
    - `docs/PRODUCT_SPEC.md:154`
  - same-family panel richness residual도 아직 남아 있습니다.
    - `AGENTS.md:47`
    - `CLAUDE.md:26`
    - `PROJECT_CUSTOM_INSTRUCTIONS.md:24`
    - `docs/ARCHITECTURE.md:11`
    - `docs/ARCHITECTURE.md:135`
    - `docs/ARCHITECTURE.md:1370`
    - `docs/PRODUCT_PROPOSAL.md:26`
    - `docs/PRODUCT_PROPOSAL.md:65`
    - `docs/project-brief.md:15`
    - `docs/project-brief.md:89`
    - `docs/NEXT_STEPS.md:21`
    - `docs/TASK_BACKLOG.md:25`
    - `docs/ACCEPTANCE_CRITERIA.md:32`
- 위 panel lines는 still-shipped truth 대비 `source role with trust level labels` 또는 `color-coded fact-strength summary bar` 같은 richer detail을 아직 생략하고 있습니다.
  - `README.md:79`
  - `docs/PRODUCT_SPEC.md:338`
  - `docs/PRODUCT_SPEC.md:361`
- 따라서 latest `/work`는 direct target 기준으로는 truthful하지만, badge-and-panel richness family closure까지는 아직 수용하기 어렵습니다.

## 검증
- `sed -n '1,240p' work/4/9/2026-04-09-docs-web-investigation-badge-panel-richness-truth-sync.md`
- `sed -n '1,240p' verify/4/9/2026-04-09-docs-remaining-claim-coverage-rendering-wording-truth-sync-verification.md`
- `git diff --check`
- `nl -ba AGENTS.md | sed -n '45,47p'`
- `nl -ba CLAUDE.md | sed -n '24,26p'`
- `nl -ba PROJECT_CUSTOM_INSTRUCTIONS.md | sed -n '22,24p'`
- `nl -ba docs/ARCHITECTURE.md | sed -n '10,11p;135,137p;1370,1372p'`
- `nl -ba docs/PRODUCT_PROPOSAL.md | sed -n '25,26p;62,65p'`
- `nl -ba docs/project-brief.md | sed -n '14,15p;86,89p'`
- `nl -ba docs/NEXT_STEPS.md | sed -n '20,21p'`
- `nl -ba docs/TASK_BACKLOG.md | sed -n '23,24p'`
- `nl -ba README.md | sed -n '78,79p'`
- `nl -ba docs/PRODUCT_SPEC.md | sed -n '152,155p'`
- `nl -ba docs/PRODUCT_SPEC.md | sed -n '338,339p;359,361p'`
- `nl -ba docs/ACCEPTANCE_CRITERIA.md | sed -n '27,32p'`
- `rg -n --no-heading 'history-card badges \\(answer-mode, verification-strength, source-role trust\\)|history-card answer-mode / verification-strength / source-role trust badges|history-card display \\(answer-mode, verification-strength, source-role trust badges\\)' README.md AGENTS.md CLAUDE.md PROJECT_CUSTOM_INSTRUCTIONS.md docs`
- `rg -n --no-heading 'claim-coverage panel with status tags, actionable hints|source role with trust level labels|fact-strength summary bar' AGENTS.md CLAUDE.md PROJECT_CUSTOM_INSTRUCTIONS.md docs/ARCHITECTURE.md docs/PRODUCT_PROPOSAL.md docs/project-brief.md docs/NEXT_STEPS.md docs/TASK_BACKLOG.md README.md docs/PRODUCT_SPEC.md`
- Python unit test와 Playwright는 재실행하지 않았습니다. 최신 `/work`가 docs-only이고 code/test/runtime 변경을 주장하지 않았기 때문입니다.

## 남은 리스크
- latest `/work`의 direct badge-richness target은 truthful합니다.
- 하지만 remaining panel-richness and source-truth badge residual이 남아 있어 same-family closure는 아직 아닙니다.
- 다음 라운드에서는 instruction docs, root summaries, `docs/PRODUCT_SPEC.md`, `docs/ACCEPTANCE_CRITERIA.md`의 remaining web-investigation richness drift를 한 번에 닫는 bounded bundle이 적절합니다.
