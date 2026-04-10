# docs: remaining claim-coverage rendering richness truth sync verification

## 변경 파일
- `verify/4/9/2026-04-09-docs-remaining-claim-coverage-rendering-richness-truth-sync-verification.md`
- `.pipeline/claude_handoff.md`

## 사용 skill
- `round-handoff`

## 변경 이유
- 최신 `/work`가 마지막 5개 target에서 claim-coverage rendering richness drift를 실제로 닫았는지 다시 확인해야 했습니다.
- 같은 날 docs-only truth-sync가 이미 길게 이어졌기 때문에, 이번 `/verify`에서는 direct target truth뿐 아니라 next slice를 또 하나의 micro-fix가 아닌 bounded bundle로 좁혀야 했습니다.

## 핵심 변경
- 최신 `/work`의 direct target은 truthful합니다.
  - `docs/PRODUCT_SPEC.md:107`
  - `docs/PRODUCT_SPEC.md:361`
  - `README.md:137`
  - `docs/NEXT_STEPS.md:22`
  - `docs/MILESTONES.md:41`
  - `docs/TASK_BACKLOG.md:26`
- 위 줄들은 richer shipped anchor와 맞습니다.
  - `README.md:79`
  - `docs/PRODUCT_SPEC.md:107`
  - `docs/PRODUCT_SPEC.md:338`
  - `docs/PRODUCT_SPEC.md:361`
- 따라서 latest `/work`가 주장한 remaining claim-coverage rendering richness closure는 수용 가능합니다.
- 다만 다음 current-surface drift는 다른 family에 남아 있습니다.
  - generic `response origin badge(s)` summary wording residual:
    - `AGENTS.md:39`
    - `CLAUDE.md:18`
    - `PROJECT_CUSTOM_INSTRUCTIONS.md:16`
    - `docs/project-brief.md:82`
    - `docs/NEXT_STEPS.md:16`
    - `docs/MILESTONES.md:35`
    - `docs/ARCHITECTURE.md:1366`
    - `docs/ACCEPTANCE_CRITERIA.md:29`
- richer shipped source-of-truth anchor는 이미 따로 있습니다.
  - `README.md:62`
  - `docs/PRODUCT_SPEC.md:105`
  - `docs/PRODUCT_SPEC.md:335`
  - `docs/PRODUCT_SPEC.md:359`
  - `docs/ACCEPTANCE_CRITERIA.md:41`
  - `docs/ACCEPTANCE_CRITERIA.md:43`
- 그래서 다음 라운드는 claim-coverage family를 더 쪼개지 말고, 남은 summary-level `response origin` shorthand를 한 번에 닫는 bounded docs bundle이 적절합니다.

## 검증
- `sed -n '1,240p' work/4/9/2026-04-09-docs-remaining-claim-coverage-rendering-richness-truth-sync.md`
- `sed -n '1,240p' verify/4/9/2026-04-09-docs-product-proposal-project-brief-acceptance-panel-richness-truth-sync-verification.md`
- `git diff --check`
- `nl -ba docs/PRODUCT_SPEC.md | sed -n '100,110p;356,363p'`
- `nl -ba README.md | sed -n '132,139p'`
- `nl -ba docs/NEXT_STEPS.md | sed -n '18,23p'; nl -ba docs/MILESTONES.md | sed -n '38,42p'; nl -ba docs/TASK_BACKLOG.md | sed -n '23,27p'`
- `rg -n --no-heading 'source role with trust level labels|fact-strength summary bar|dedicated plain-language' README.md docs/PRODUCT_SPEC.md docs/NEXT_STEPS.md docs/MILESTONES.md docs/TASK_BACKLOG.md AGENTS.md CLAUDE.md PROJECT_CUSTOM_INSTRUCTIONS.md docs/ARCHITECTURE.md docs/PRODUCT_PROPOSAL.md docs/project-brief.md docs/ACCEPTANCE_CRITERIA.md`
- `nl -ba README.md | sed -n '58,63p;77,80p'; nl -ba docs/PRODUCT_SPEC.md | sed -n '332,339p;357,362p'`
- `nl -ba AGENTS.md | sed -n '39,48p'`
- `nl -ba CLAUDE.md | sed -n '18,27p'`
- `nl -ba PROJECT_CUSTOM_INSTRUCTIONS.md | sed -n '16,25p'`
- `rg -n --no-heading '^- response origin badge|^- response-origin badges|^- response origin badges|^  - response origin badge|^  - response-origin badges|^  - response origin badges' README.md AGENTS.md CLAUDE.md PROJECT_CUSTOM_INSTRUCTIONS.md docs/*.md`
- `nl -ba docs/project-brief.md | sed -n '80,83p'`
- `nl -ba docs/NEXT_STEPS.md | sed -n '15,16p'`
- `nl -ba docs/MILESTONES.md | sed -n '35,35p'`
- `nl -ba docs/ACCEPTANCE_CRITERIA.md | sed -n '28,29p;41,43p'`
- `nl -ba docs/ARCHITECTURE.md | sed -n '1365,1367p'`
- Python unit test와 Playwright는 재실행하지 않았습니다. 최신 `/work`가 docs-only이고 code/test/runtime 변경을 주장하지 않았기 때문입니다.

## 남은 리스크
- latest `/work`의 direct target은 truthful하고, remaining claim-coverage rendering richness family closure도 수용 가능합니다.
- 남은 drift는 adjacent current-summary family입니다. 여러 active docs가 아직 shipped web-investigation origin detail을 generic `response origin badge(s)` 수준으로만 축약하고 있습니다.
- 다음 라운드는 `AGENTS.md`, `CLAUDE.md`, `PROJECT_CUSTOM_INSTRUCTIONS.md`, `docs/project-brief.md`, `docs/NEXT_STEPS.md`, `docs/MILESTONES.md`, `docs/ARCHITECTURE.md`, `docs/ACCEPTANCE_CRITERIA.md`의 summary-level response-origin richness를 한 번에 맞추는 bounded bundle이 적절합니다.
