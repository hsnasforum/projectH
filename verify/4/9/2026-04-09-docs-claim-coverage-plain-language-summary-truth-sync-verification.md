# docs: claim-coverage plain-language summary truth sync verification

## 변경 파일
- `verify/4/9/2026-04-09-docs-claim-coverage-plain-language-summary-truth-sync-verification.md`
- `.pipeline/claude_handoff.md`

## 사용 skill
- `round-handoff`

## 변경 이유
- 최신 `/work`가 claim-coverage plain-language wording bundle의 직접 수정 대상을 실제로 shipped truth에 맞췄는지 다시 확인해야 했습니다.
- direct target이 truthful하더라도, `/work`가 주장한 repo-wide family closure까지 맞는지는 별도로 좁게 재검증해야 했습니다.

## 핵심 변경
- 최신 `/work`의 직접 수정 대상은 truthful합니다.
  - `AGENTS.md:47`
  - `CLAUDE.md:26`
  - `PROJECT_CUSTOM_INSTRUCTIONS.md:24`
  - `docs/ARCHITECTURE.md:11`
  - `docs/ARCHITECTURE.md:135`
  - `docs/ARCHITECTURE.md:1370`
  - `docs/PRODUCT_PROPOSAL.md:26`
  - `docs/project-brief.md:15`
  - `docs/PRODUCT_SPEC.md:155`
- 현재 문구는 이미 남아 있던 fuller shipped wording anchor와 맞습니다.
  - `README.md:79`
  - `docs/PRODUCT_SPEC.md:107`
  - `docs/PRODUCT_SPEC.md:155`
  - `docs/PRODUCT_SPEC.md:361`
  - `docs/NEXT_STEPS.md:21`
  - `docs/project-brief.md:89`
  - `docs/PRODUCT_PROPOSAL.md:65`
- 다만 latest `/work`의 `남은 리스크 없음`과 `전체 repo docs의 claim-coverage plain-language summary 동기화 완료` 주장은 과합니다.
  - same-family generic rendering wording이 아직 남아 있습니다.
    - `README.md:137`
    - `docs/ACCEPTANCE_CRITERIA.md:1365`
    - `docs/MILESTONES.md:41`
    - `docs/NEXT_STEPS.md:22`
    - `docs/TASK_BACKLOG.md:26`
- 따라서 latest `/work`는 direct target 기준으로는 truthful하지만, repo-wide same-family closure까지는 아직 수용하기 어렵습니다.

## 검증
- `sed -n '1,240p' work/4/9/2026-04-09-docs-claim-coverage-plain-language-summary-truth-sync.md`
- `sed -n '1,220p' verify/4/9/2026-04-09-docs-instruction-web-investigation-strong-badge-downgrade-truth-sync-verification.md`
- `nl -ba AGENTS.md | sed -n '44,48p'`
- `nl -ba CLAUDE.md | sed -n '23,27p'`
- `nl -ba PROJECT_CUSTOM_INSTRUCTIONS.md | sed -n '21,25p'`
- `nl -ba docs/ARCHITECTURE.md | sed -n '9,12p'`
- `nl -ba docs/ARCHITECTURE.md | sed -n '132,138p'`
- `nl -ba docs/ARCHITECTURE.md | sed -n '1368,1373p'`
- `nl -ba docs/PRODUCT_PROPOSAL.md | sed -n '24,27p'`
- `nl -ba docs/project-brief.md | sed -n '13,16p'`
- `nl -ba README.md | sed -n '76,80p'`
- `nl -ba README.md | sed -n '136,138p'`
- `nl -ba docs/PRODUCT_SPEC.md | sed -n '152,156p'`
- `nl -ba docs/PRODUCT_SPEC.md | sed -n '338,361p'`
- `nl -ba docs/NEXT_STEPS.md | sed -n '20,22p'`
- `nl -ba docs/MILESTONES.md | sed -n '40,42p'`
- `nl -ba docs/ACCEPTANCE_CRITERIA.md | sed -n '1364,1366p'`
- `nl -ba docs/TASK_BACKLOG.md | sed -n '22,26p'`
- `rg -n --no-heading 'focus-slot reinvestigation explanation' README.md AGENTS.md CLAUDE.md PROJECT_CUSTOM_INSTRUCTIONS.md docs`
- `rg -n --no-heading 'history-card badges \\(answer-mode, verification-strength, source-role trust\\)|fact-strength summary bar|verification-strength summary bar|source-role with trust level labels|source-role trust labels' README.md AGENTS.md CLAUDE.md PROJECT_CUSTOM_INSTRUCTIONS.md docs`
- `git diff --check`
- Python unit test와 Playwright는 재실행하지 않았습니다. 최신 `/work`가 docs-only이고 code/test/runtime 변경을 주장하지 않았기 때문입니다.

## 남은 리스크
- latest `/work`의 direct target은 truthful합니다.
- 하지만 same-family rendering-contract / smoke wording residual이 남아 있어 repo-wide closure는 아직 아닙니다.
- 다음 라운드에서는 `README.md`, `docs/ACCEPTANCE_CRITERIA.md`, `docs/MILESTONES.md`, `docs/NEXT_STEPS.md`, `docs/TASK_BACKLOG.md`의 remaining claim-coverage rendering wording을 한 번에 닫는 편이 가장 bounded한 후속 slice입니다.
