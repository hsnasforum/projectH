# docs: top-level next-phase reviewed-memory boundary truth sync verification

## 변경 파일
- `verify/4/9/2026-04-09-docs-top-level-next-phase-reviewed-memory-boundary-truth-sync-verification.md`
- `.pipeline/claude_handoff.md`

## 사용 skill
- `round-handoff`

## 변경 이유
- 최신 `/work`가 `README.md`, `docs/project-brief.md`, `docs/PRODUCT_PROPOSAL.md`, `docs/ARCHITECTURE.md`, `docs/MILESTONES.md`, `docs/TASK_BACKLOG.md`의 top-level `next phase` / reviewed-memory boundary wording을 현재 shipped truth와 맞게 정리했는지 다시 확인해야 했습니다.
- direct target이 truthful하면, 다음은 current reviewed-memory surface가 아직 top-level current-product summaries에 빠진 residual을 한 번에 닫는 bounded bundle로 가는 편이 더 적절했습니다.

## 핵심 변경
- 최신 `/work`의 직접 수정 대상은 truthful합니다.
  - `README.md:32`
  - `docs/project-brief.md:19`
  - `docs/PRODUCT_PROPOSAL.md:93`
  - `docs/ARCHITECTURE.md:14`
  - `docs/MILESTONES.md:10`
  - `docs/TASK_BACKLOG.md:8`
- 현재 문구는 shipped reviewed-memory / review-queue boundary와 맞습니다.
  - `README.md:67`
  - `README.md:68`
  - `docs/PRODUCT_SPEC.md:58`
  - `docs/PRODUCT_SPEC.md:60`
  - `docs/PRODUCT_SPEC.md:1520`
  - `docs/PRODUCT_SPEC.md:1539`
  - `docs/PRODUCT_SPEC.md:1562`
  - `docs/ARCHITECTURE.md:29`
  - `docs/ARCHITECTURE.md:79`
  - `docs/ARCHITECTURE.md:80`
  - `app/templates/index.html:24`
  - `app/templates/index.html:29`
  - `app/serializers.py:250`
  - `app/serializers.py:1586`
  - `app/handlers/chat.py:456`
  - `app/handlers/aggregate.py:257`
  - `app/handlers/aggregate.py:639`
  - `app/static/app.js:2837`
  - `app/static/app.js:3142`
  - `tests/test_web_app.py:166`
  - `tests/test_web_app.py:170`
  - `tests/test_web_app.py:7300`
- same-family top-level `next phase` / reviewed-memory boundary drift는 이번 라운드로 닫힌 것으로 봐도 무방합니다.
- 다만 최신 `/work`의 `남은 리스크`는 약간 좁습니다.
  - current reviewed-memory surface가 아직 top-level current-product summaries에는 일부 빠져 있습니다.
    - `README.md:46`
    - `AGENTS.md:29`
    - `CLAUDE.md:9`
    - `PROJECT_CUSTOM_INSTRUCTIONS.md:6`
    - `docs/NEXT_STEPS.md:5`
    - `docs/ACCEPTANCE_CRITERIA.md:25`
  - 위 구간들은 response-feedback / grounded-brief surface까지는 반영했지만, shipped review queue (`검토 후보`)와 aggregate apply trigger (`검토 메모 적용 후보`) 및 reviewed-memory apply lifecycle은 아직 top-level current-surface summary에 포함하지 않습니다.
- 따라서 latest `/work` 자체는 truthful하지만, `AGENTS.md`, `CLAUDE.md`, `PROJECT_CUSTOM_INSTRUCTIONS.md`만 잔여라는 closeout wording은 조금 좁았습니다.
- 다음 슬라이스는 `README.md`, `AGENTS.md`, `CLAUDE.md`, `PROJECT_CUSTOM_INSTRUCTIONS.md`, `docs/NEXT_STEPS.md`, `docs/ACCEPTANCE_CRITERIA.md`를 한 번에 묶어 top-level current-surface reviewed-memory summary truth를 맞추는 bounded bundle이 적절합니다.

## 검증
- `git diff --check`
- `nl -ba README.md | sed -n '32,42p'`
- `nl -ba docs/project-brief.md | sed -n '19,28p'`
- `nl -ba docs/PRODUCT_PROPOSAL.md | sed -n '93,106p'`
- `nl -ba docs/ARCHITECTURE.md | sed -n '14,22p'`
- `nl -ba docs/MILESTONES.md | sed -n '10,18p'`
- `nl -ba docs/TASK_BACKLOG.md | sed -n '7,12p'`
- `git diff -- README.md docs/project-brief.md docs/PRODUCT_PROPOSAL.md docs/ARCHITECTURE.md docs/MILESTONES.md docs/TASK_BACKLOG.md`
- `rg -n --no-heading 'Current Reviewed-Memory Boundary|current reviewed-memory boundary|first reviewed-memory slice is shipped|next phase extends the shipped reviewed-memory boundary|broader structured correction memory|durable preference memory|cross-session memory remains later' README.md docs/*.md AGENTS.md CLAUDE.md PROJECT_CUSTOM_INSTRUCTIONS.md GEMINI.md`
- `rg -n --no-heading 'next phase is a correction / approval / preference memory layer|next phase target: correction / approval / preference memory|the next phase adds a correction / approval / preference memory layer|The next phase is a correction / approval / preference memory layer|correction / approval / preference memory layer' README.md docs/*.md AGENTS.md CLAUDE.md PROJECT_CUSTOM_INSTRUCTIONS.md GEMINI.md`
- `nl -ba README.md | sed -n '46,58p'`
- `nl -ba AGENTS.md | sed -n '29,48p'`
- `nl -ba CLAUDE.md | sed -n '9,27p'`
- `nl -ba PROJECT_CUSTOM_INSTRUCTIONS.md | sed -n '6,24p'`
- `nl -ba docs/NEXT_STEPS.md | sed -n '5,18p'`
- `nl -ba docs/ACCEPTANCE_CRITERIA.md | sed -n '23,31p'`
- `rg -n --no-heading 'review queue|검토 후보|검토 메모 적용 후보|Current Reviewed-Memory Boundary|current reviewed-memory boundary|aggregate apply trigger' README.md AGENTS.md CLAUDE.md PROJECT_CUSTOM_INSTRUCTIONS.md docs/NEXT_STEPS.md docs/MILESTONES.md`
- Python unit test와 Playwright는 재실행하지 않았습니다. 최신 `/work`가 docs-only이고 code/test/runtime 변경을 주장하지 않았기 때문입니다.

## 남은 리스크
- 최신 `/work`의 직접 수정 대상과 next-phase boundary 정리는 truthful합니다.
- 다만 current reviewed-memory surface를 top-level current-product summaries에 반영하는 잔여 bundle이 남아 있습니다.
- 다음 라운드에서 위 6개 파일을 함께 맞추면, current shipped reviewed-memory surface와 next/later memory layers의 구분이 top-level current-surface summary에도 더 정직하게 반영됩니다.
