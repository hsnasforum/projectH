# docs: current-surface reviewed-memory summary truth sync verification

## 변경 파일
- `verify/4/9/2026-04-09-docs-current-surface-reviewed-memory-summary-truth-sync-verification.md`
- `.pipeline/claude_handoff.md`

## 사용 skill
- `round-handoff`

## 변경 이유
- 최신 `/work`가 `README.md`, `AGENTS.md`, `CLAUDE.md`, `PROJECT_CUSTOM_INSTRUCTIONS.md`, `docs/NEXT_STEPS.md`, `docs/ACCEPTANCE_CRITERIA.md`의 top-level current-surface 요약에 shipped reviewed-memory surface를 반영했다고 주장하므로, direct target truth부터 다시 확인해야 했습니다.
- same-day docs-only truth-sync가 길게 이어진 상태라, direct target이 truthful하더라도 다음은 남은 같은 family residual을 한 번에 닫는 bounded bundle로 정해야 했습니다.

## 핵심 변경
- 최신 `/work`의 직접 수정 대상은 truthful합니다.
  - `README.md:48`
  - `AGENTS.md:48`
  - `CLAUDE.md:27`
  - `PROJECT_CUSTOM_INSTRUCTIONS.md:25`
  - `docs/NEXT_STEPS.md:19`
  - `docs/ACCEPTANCE_CRITERIA.md:25`
- 위 문구는 현재 shipped reviewed-memory surface와 맞습니다.
  - `docs/PRODUCT_SPEC.md:58`
  - `docs/PRODUCT_SPEC.md:60`
  - `docs/PRODUCT_SPEC.md:1520`
  - `docs/PRODUCT_SPEC.md:1539`
  - `docs/PRODUCT_SPEC.md:1562`
  - `docs/ARCHITECTURE.md:15`
  - `docs/ARCHITECTURE.md:85`
  - `app/templates/index.html:24`
  - `app/templates/index.html:29`
  - `tests/test_web_app.py:166`
  - `tests/test_web_app.py:170`
  - `tests/test_web_app.py:7300`
- 다만 최신 `/work`의 `남은 리스크 없음`은 성립하지 않습니다.
  - 같은 current-surface / current-contract summary family residual이 아직 남아 있습니다.
    - `README.md:11`
    - `docs/PRODUCT_SPEC.md:18`
    - `docs/PRODUCT_SPEC.md:27`
    - `docs/ARCHITECTURE.md:10`
    - `docs/MILESTONES.md:6`
    - `docs/project-brief.md:15`
    - `docs/PRODUCT_PROPOSAL.md:25`
  - 위 구간들은 response-feedback / grounded-brief surface까지는 top-level current contract에 반영하지만, 이미 shipped된 review queue (`검토 후보`), aggregate apply trigger (`검토 메모 적용 후보`), reviewed-memory active-effect path는 아직 같은 층위의 요약에 포함하지 않습니다.
- 따라서 latest `/work` 자체는 truthful하지만, same-family closure 주장까지는 받아들이기 어렵습니다.
- 다음 슬라이스는 `README.md`, `docs/PRODUCT_SPEC.md`, `docs/ARCHITECTURE.md`, `docs/MILESTONES.md`, `docs/project-brief.md`, `docs/PRODUCT_PROPOSAL.md`를 함께 묶어 top-level current-contract reviewed-memory surface wording을 맞추는 bounded bundle이 적절합니다.

## 검증
- `sed -n '1,220p' work/4/9/2026-04-09-docs-current-surface-reviewed-memory-summary-truth-sync.md`
- `sed -n '1,220p' verify/4/9/2026-04-09-docs-top-level-next-phase-reviewed-memory-boundary-truth-sync-verification.md`
- `git diff --check`
- `git diff -- README.md AGENTS.md CLAUDE.md PROJECT_CUSTOM_INSTRUCTIONS.md docs/NEXT_STEPS.md docs/ACCEPTANCE_CRITERIA.md`
- `nl -ba README.md | sed -n '44,55p'`
- `nl -ba AGENTS.md | sed -n '29,52p'`
- `nl -ba CLAUDE.md | sed -n '9,30p'`
- `nl -ba PROJECT_CUSTOM_INSTRUCTIONS.md | sed -n '6,28p'`
- `nl -ba docs/NEXT_STEPS.md | sed -n '5,20p'`
- `nl -ba docs/ACCEPTANCE_CRITERIA.md | sed -n '23,31p'`
- `rg -n --no-heading '검토 후보|검토 메모 적용 후보|review queue|aggregate apply trigger|reviewed-memory active|reviewed-memory effect|effect can become active' README.md AGENTS.md CLAUDE.md PROJECT_CUSTOM_INSTRUCTIONS.md docs/NEXT_STEPS.md docs/ACCEPTANCE_CRITERIA.md docs/PRODUCT_SPEC.md docs/ARCHITECTURE.md app/templates/index.html app/static/app.js app/handlers/aggregate.py app/serializers.py tests/test_web_app.py`
- `nl -ba docs/PRODUCT_SPEC.md | sed -n '1,35p'`
- `nl -ba docs/ARCHITECTURE.md | sed -n '1,22p'`
- `nl -ba docs/MILESTONES.md | sed -n '1,20p'`
- `nl -ba docs/TASK_BACKLOG.md | sed -n '1,15p'`
- `nl -ba docs/project-brief.md | sed -n '1,24p'`
- `nl -ba docs/PRODUCT_PROPOSAL.md | sed -n '1,32p'`
- `rg -n --no-heading 'Current Product|Current Contract|Facts|One-Line Current Product Definition|Product Framing|Current Product Slice|Current implemented focus|현재 구현 기준의 중심|browser MVP already covers|Current Product Identity' README.md AGENTS.md CLAUDE.md PROJECT_CUSTOM_INSTRUCTIONS.md docs/*.md`
- `nl -ba docs/PRODUCT_SPEC.md | sed -n '16,29p'`
- `nl -ba docs/ARCHITECTURE.md | sed -n '9,16p'`
- `nl -ba docs/MILESTONES.md | sed -n '5,12p'`
- `nl -ba docs/project-brief.md | sed -n '13,20p'`
- `nl -ba docs/PRODUCT_PROPOSAL.md | sed -n '24,27p'`
- `nl -ba README.md | sed -n '1,15p'`
- Python unit test와 Playwright는 재실행하지 않았습니다. 최신 `/work`가 docs-only이고 code/test/runtime 변경을 주장하지 않았기 때문입니다.

## 남은 리스크
- 최신 `/work`의 직접 수정 대상은 truthful하지만, current-surface reviewed-memory summary family는 아직 완전히 닫히지 않았습니다.
- 다음 라운드에서 위 6개 파일의 top-level current-contract/current-product wording을 함께 맞추면, response-feedback / grounded-brief와 reviewed-memory first slice가 같은 현재 shipped 층위에서 더 정직하게 정렬됩니다.
