# docs: remaining reviewed-memory feature-list shorthand truth sync verification

## 변경 파일
- `verify/4/9/2026-04-09-docs-reviewed-memory-feature-list-shorthand-truth-sync-verification.md`
- `.pipeline/claude_handoff.md`

## 사용 skill
- `round-handoff`

## 변경 이유
- 최신 `/work`가 남아 있던 reviewed-memory feature-list shorthand 5줄을 실제로 current shipped lifecycle wording과 맞췄는지 다시 확인해야 했습니다.
- direct target이 truthful하면, 이 family는 닫고 다음 docs axis로 넘어가는 편이 맞았습니다.

## 핵심 변경
- 최신 `/work`의 직접 수정 대상은 truthful합니다.
  - `AGENTS.md:48`
  - `CLAUDE.md:27`
  - `PROJECT_CUSTOM_INSTRUCTIONS.md:25`
  - `docs/project-brief.md:15`
  - `docs/ACCEPTANCE_CRITERIA.md:25`
- 현재 문구는 shipped reviewed-memory lifecycle truth와 맞습니다.
  - `app/handlers/aggregate.py:399`
  - `app/handlers/aggregate.py:470`
  - `app/handlers/aggregate.py:532`
  - `app/handlers/aggregate.py:639`
  - `docs/ARCHITECTURE.md:15`
  - `docs/MILESTONES.md:11`
  - `docs/PRODUCT_PROPOSAL.md:95`
  - `docs/TASK_BACKLOG.md:8`
- `reviewed-memory active-effect path` residual은 현재 active docs 기준으로 0건입니다.
- 따라서 reviewed-memory lifecycle shorthand family closure는 수용 가능합니다.
- 다음 슬라이스는 new quality axis로 넘어가는 편이 적절합니다.
  - 현재 instruction docs의 current-product slice는 web-investigation current surface를 요약하면서 entity-card strong-badge downgrade를 아직 빠뜨리고 있습니다.
    - `AGENTS.md:45`
    - `AGENTS.md:46`
    - `AGENTS.md:47`
    - `CLAUDE.md:24`
    - `CLAUDE.md:25`
    - `CLAUDE.md:26`
    - `PROJECT_CUSTOM_INSTRUCTIONS.md:22`
    - `PROJECT_CUSTOM_INSTRUCTIONS.md:23`
    - `PROJECT_CUSTOM_INSTRUCTIONS.md:24`
  - shipped truth anchor는 이미 아래에 명시돼 있고 구현/테스트도 받쳐 줍니다.
    - `README.md:78`
    - `docs/PRODUCT_SPEC.md:155`
    - `docs/ACCEPTANCE_CRITERIA.md:41`
    - `app/static/app.js:2276`
    - `tests/test_smoke.py:1711`
    - `tests/test_web_app.py:9254`

## 검증
- `git diff --check`
- `git diff -- AGENTS.md CLAUDE.md PROJECT_CUSTOM_INSTRUCTIONS.md docs/project-brief.md docs/ACCEPTANCE_CRITERIA.md`
- `sed -n '1,260p' work/4/9/2026-04-09-docs-reviewed-memory-feature-list-shorthand-truth-sync.md`
- `sed -n '1,260p' verify/4/9/2026-04-09-docs-reviewed-memory-lifecycle-shorthand-residual-truth-sync-verification.md`
- `rg -n --no-heading 'reviewed-memory active-effect path|active-effect path' README.md AGENTS.md CLAUDE.md PROJECT_CUSTOM_INSTRUCTIONS.md docs`
- `rg -n --no-heading 'reviewed-memory active-effect path' README.md AGENTS.md CLAUDE.md PROJECT_CUSTOM_INSTRUCTIONS.md docs`
- `nl -ba AGENTS.md | sed -n '44,49p'`
- `nl -ba CLAUDE.md | sed -n '23,28p'`
- `nl -ba PROJECT_CUSTOM_INSTRUCTIONS.md | sed -n '21,26p'`
- `nl -ba docs/project-brief.md | sed -n '13,16p'`
- `nl -ba docs/ACCEPTANCE_CRITERIA.md | sed -n '23,26p'`
- `nl -ba app/handlers/aggregate.py | sed -n '388,406p'`
- `nl -ba app/handlers/aggregate.py | sed -n '466,474p'`
- `nl -ba app/handlers/aggregate.py | sed -n '528,536p'`
- `nl -ba app/handlers/aggregate.py | sed -n '636,644p'`
- `nl -ba app/static/app.js | sed -n '2272,2298p'`
- `nl -ba tests/test_smoke.py | sed -n '1710,1756p'`
- `nl -ba tests/test_web_app.py | sed -n '9248,9260p'`
- `nl -ba README.md | sed -n '78,79p'`
- `nl -ba docs/PRODUCT_SPEC.md | sed -n '154,155p'`
- `nl -ba docs/ACCEPTANCE_CRITERIA.md | sed -n '40,41p'`
- Python unit test와 Playwright는 재실행하지 않았습니다. 최신 `/work`가 docs-only이고 code/test/runtime 변경을 주장하지 않았기 때문입니다.

## 남은 리스크
- 최신 `/work`의 direct target은 truthful하고 reviewed-memory lifecycle shorthand family도 active docs 기준으로 닫혔습니다.
- 다음 current-risk reduction은 instruction docs current-product slice가 아직 빠뜨리는 web-investigation `entity-card strong-badge downgrade` nuance입니다.
