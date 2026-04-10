# docs: AGENTS CLAUDE PROJECT_CUSTOM_INSTRUCTIONS web-investigation strong-badge downgrade truth sync verification

## 변경 파일
- `verify/4/9/2026-04-09-docs-instruction-web-investigation-strong-badge-downgrade-truth-sync-verification.md`
- `.pipeline/claude_handoff.md`

## 사용 skill
- `round-handoff`

## 변경 이유
- 최신 `/work`가 instruction docs 3곳의 web-investigation current-product summary에 shipped `entity-card strong-badge downgrade` nuance를 실제로 반영했는지 다시 확인해야 했습니다.
- direct target이 truthful하더라도, 같은 current-summary family에 더 넓은 residual이 남아 있으면 `남은 리스크 없음`은 그대로 수용하면 안 됐습니다.

## 핵심 변경
- 최신 `/work`의 직접 수정 대상은 truthful합니다.
  - `AGENTS.md:46`
  - `CLAUDE.md:25`
  - `PROJECT_CUSTOM_INSTRUCTIONS.md:23`
- 현재 문구는 shipped web-investigation truth와 맞습니다.
  - `README.md:78`
  - `docs/PRODUCT_SPEC.md:155`
  - `docs/ACCEPTANCE_CRITERIA.md:41`
  - `app/static/app.js:2276`
  - `tests/test_smoke.py:1711`
  - `tests/test_web_app.py:9254`
- 따라서 latest `/work`의 direct target은 truthful합니다.
- 다만 latest `/work`의 `남은 리스크 없음`은 과합니다.
  - 같은 web-investigation current-summary family 안에 아직 generic `focus-slot reinvestigation explanation` wording이 남아 있습니다.
    - `AGENTS.md:47`
    - `CLAUDE.md:26`
    - `PROJECT_CUSTOM_INSTRUCTIONS.md:24`
    - `docs/ARCHITECTURE.md:11`
    - `docs/PRODUCT_PROPOSAL.md:26`
    - `docs/project-brief.md:15`
    - `docs/PRODUCT_SPEC.md:155`
  - 반면 fuller shipped wording은 이미 아래에 잡혀 있습니다.
    - `README.md:79`
    - `docs/NEXT_STEPS.md:21`
    - `docs/project-brief.md:89`
    - `docs/PRODUCT_PROPOSAL.md:65`
    - `docs/PRODUCT_SPEC.md:107`
    - `docs/PRODUCT_SPEC.md:361`
- 따라서 latest `/work`는 direct target 기준으로는 truthful하지만, instruction-doc web-investigation current-summary family closure까지는 아직 수용하기 어렵습니다.

## 검증
- `git diff --check`
- `sed -n '1,240p' work/4/9/2026-04-09-docs-instruction-web-investigation-strong-badge-downgrade-truth-sync.md`
- `sed -n '1,260p' verify/4/9/2026-04-09-docs-reviewed-memory-feature-list-shorthand-truth-sync-verification.md`
- `nl -ba AGENTS.md | sed -n '44,47p'`
- `nl -ba CLAUDE.md | sed -n '24,27p'`
- `nl -ba PROJECT_CUSTOM_INSTRUCTIONS.md | sed -n '22,25p'`
- `nl -ba README.md | sed -n '78,79p'`
- `nl -ba docs/PRODUCT_SPEC.md | sed -n '154,155p'`
- `nl -ba docs/ACCEPTANCE_CRITERIA.md | sed -n '40,41p'`
- `nl -ba docs/NEXT_STEPS.md | sed -n '21,21p'`
- `nl -ba docs/project-brief.md | sed -n '88,89p'`
- `nl -ba app/static/app.js | sed -n '2273,2298p'`
- `nl -ba tests/test_smoke.py | sed -n '1711,1755p'`
- `nl -ba tests/test_web_app.py | sed -n '9250,9255p'`
- `rg -n --no-heading 'entity-card / latest-update answer-mode distinction with separate verification labels' README.md AGENTS.md CLAUDE.md PROJECT_CUSTOM_INSTRUCTIONS.md docs`
- `rg -n --no-heading 'entity-card strong-badge downgrade|verification badge is downgraded from strong|no claim slot has cross-verified status' README.md AGENTS.md CLAUDE.md PROJECT_CUSTOM_INSTRUCTIONS.md docs`
- `rg -n --no-heading 'claim-coverage panel with status tags, actionable hints, and focus-slot reinvestigation explanation|dedicated plain-language focus-slot reinvestigation explanation|plain-language focus-slot reinvestigation explanation' AGENTS.md CLAUDE.md PROJECT_CUSTOM_INSTRUCTIONS.md README.md docs`
- Python unit test와 Playwright는 재실행하지 않았습니다. 최신 `/work`가 docs-only이고 code/test/runtime 변경을 주장하지 않았기 때문입니다.

## 남은 리스크
- 최신 `/work`의 direct target은 truthful합니다.
- 하지만 same-family current-summary wording residual이 아직 남아 있어 `남은 리스크 없음`은 그대로 수용하기 어렵습니다.
- 다음 라운드에서 instruction docs와 root current-product summaries의 `claim-coverage` plain-language explanation wording을 한 번에 맞추면, 이 web-investigation summary family를 더 정직하게 닫을 수 있습니다.
