# docs: remaining claim-coverage rendering wording truth sync verification

## 변경 파일
- `verify/4/9/2026-04-09-docs-remaining-claim-coverage-rendering-wording-truth-sync-verification.md`
- `.pipeline/claude_handoff.md`

## 사용 skill
- `round-handoff`

## 변경 이유
- 최신 `/work`가 남아 있던 claim-coverage rendering wording 5곳을 실제로 shipped wording에 맞췄는지 다시 확인해야 했습니다.
- direct target이 truthful하면 이 family를 닫고, 다음 docs-only slice도 같은 web-investigation current-surface family 안에서 한 번에 고르는 편이 맞았습니다.

## 핵심 변경
- 최신 `/work`의 직접 수정 대상은 truthful합니다.
  - `README.md:137`
  - `docs/ACCEPTANCE_CRITERIA.md:1365`
  - `docs/MILESTONES.md:41`
  - `docs/NEXT_STEPS.md:22`
  - `docs/TASK_BACKLOG.md:26`
- 현재 문구는 shipped anchor와 맞습니다.
  - `README.md:79`
  - `docs/PRODUCT_SPEC.md:107`
  - `docs/PRODUCT_SPEC.md:342`
  - `docs/PRODUCT_SPEC.md:361`
- generic `focus-slot reinvestigation explanation` residual은 active docs 기준으로 0건입니다.
- 따라서 latest `/work`의 `전체 repo docs의 claim-coverage rendering wording 동기화 완료` 주장은 수용 가능합니다.
- 다음 same-family docs drift는 wording qualifier 자체가 아니라 current-surface richness compression입니다.
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
- 이 줄들은 still-shipped web-investigation surface를 `history-card badges (answer-mode, verification-strength, source-role trust)` 수준으로만 압축하고 있어, richer truth anchor인 `README.md:78`, `README.md:79`, `docs/PRODUCT_SPEC.md:338`, `docs/PRODUCT_SPEC.md:339`, `docs/PRODUCT_SPEC.md:359`, `docs/PRODUCT_SPEC.md:361`과 아직 간격이 있습니다.

## 검증
- `sed -n '1,240p' work/4/9/2026-04-09-docs-remaining-claim-coverage-rendering-wording-truth-sync.md`
- `sed -n '1,240p' verify/4/9/2026-04-09-docs-claim-coverage-plain-language-summary-truth-sync-verification.md`
- `nl -ba README.md | sed -n '136,138p'`
- `nl -ba docs/ACCEPTANCE_CRITERIA.md | sed -n '1364,1366p'`
- `nl -ba docs/MILESTONES.md | sed -n '40,42p'`
- `nl -ba docs/NEXT_STEPS.md | sed -n '21,22p'`
- `nl -ba docs/TASK_BACKLOG.md | sed -n '25,26p'`
- `nl -ba docs/PRODUCT_SPEC.md | sed -n '107,107p;338,342p;361,361p'`
- `rg -n --no-heading 'focus-slot reinvestigation explanation' README.md AGENTS.md CLAUDE.md PROJECT_CUSTOM_INSTRUCTIONS.md docs`
- `bash -lc "rg -n --no-heading 'focus-slot reinvestigation explanation' README.md AGENTS.md CLAUDE.md PROJECT_CUSTOM_INSTRUCTIONS.md docs | rg -v 'dedicated plain-language' || true"`
- `rg -n --no-heading 'history-card badges \\(answer-mode, verification-strength, source-role trust\\)|color-coded verification-strength badges|color-coded source-role trust badges|fact-strength summary bar above the response text|source role with trust level labels' README.md AGENTS.md CLAUDE.md PROJECT_CUSTOM_INSTRUCTIONS.md docs`
- `nl -ba AGENTS.md | sed -n '45,47p'`
- `nl -ba CLAUDE.md | sed -n '24,26p'`
- `nl -ba PROJECT_CUSTOM_INSTRUCTIONS.md | sed -n '22,24p'`
- `nl -ba docs/PRODUCT_PROPOSAL.md | sed -n '25,26p;60,65p'`
- `nl -ba docs/project-brief.md | sed -n '14,15p;84,89p'`
- `nl -ba docs/ARCHITECTURE.md | sed -n '10,11p;135,137p;1370,1372p'`
- `git diff --check`
- Python unit test와 Playwright는 재실행하지 않았습니다. 최신 `/work`가 docs-only이고 code/test/runtime 변경을 주장하지 않았기 때문입니다.

## 남은 리스크
- latest `/work`의 direct target은 truthful하고 claim-coverage rendering wording family closure도 수용 가능합니다.
- 다만 adjacent same-family current-surface summary docs가 still-shipped badge/panel richness를 충분히 드러내지 못하는 압축 표현을 유지하고 있습니다.
- 다음 라운드에서는 instruction docs와 root/docs summaries의 remaining web-investigation badge-and-panel richness를 한 번에 맞추는 bounded bundle이 적절합니다.
