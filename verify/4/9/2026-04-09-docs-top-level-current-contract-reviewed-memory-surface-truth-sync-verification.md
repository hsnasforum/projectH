# docs: top-level current-contract reviewed-memory surface truth sync verification

## 변경 파일
- `verify/4/9/2026-04-09-docs-top-level-current-contract-reviewed-memory-surface-truth-sync-verification.md`
- `.pipeline/claude_handoff.md`

## 사용 skill
- `round-handoff`

## 변경 이유
- 최신 `/work`가 `README.md`, `docs/PRODUCT_SPEC.md`, `docs/ARCHITECTURE.md`, `docs/MILESTONES.md`, `docs/project-brief.md`, `docs/PRODUCT_PROPOSAL.md`의 top-level current-contract reviewed-memory surface wording을 현재 shipped truth와 맞췄다고 주장하므로, direct target truth부터 다시 확인해야 했습니다.
- direct target이 truthful하더라도, same-day docs-only truth-sync가 길게 이어진 상태라 같은 family residual이 남는다면 더 작은 micro-slice가 아니라 한 번에 닫히는 bounded bundle로 넘겨야 했습니다.

## 핵심 변경
- 최신 `/work`의 직접 수정 대상은 truthful합니다.
  - `README.md:12`
  - `docs/PRODUCT_SPEC.md:18`
  - `docs/PRODUCT_SPEC.md:27`
  - `docs/ARCHITECTURE.md:10`
  - `docs/MILESTONES.md:6`
  - `docs/project-brief.md:14`
  - `docs/project-brief.md:15`
  - `docs/PRODUCT_PROPOSAL.md:25`
- 위 문구는 현재 shipped reviewed-memory surface와 맞습니다.
  - `docs/PRODUCT_SPEC.md:58`
  - `docs/PRODUCT_SPEC.md:60`
  - `docs/ARCHITECTURE.md:15`
  - `docs/ARCHITECTURE.md:85`
  - `app/templates/index.html:24`
  - `app/templates/index.html:29`
  - `tests/test_web_app.py:166`
  - `tests/test_web_app.py:170`
  - `tests/test_web_app.py:7300`
- 다만 최신 `/work`의 `남은 리스크 없음`은 약간 과합니다.
  - 상단 one-line current-identity / status 계층에는 같은 family residual이 남아 있습니다.
    - `README.md:3`
    - `CLAUDE.md:5`
    - `PROJECT_CUSTOM_INSTRUCTIONS.md:1`
    - `docs/project-brief.md:5`
    - `docs/PRODUCT_PROPOSAL.md:6`
    - `docs/PRODUCT_PROPOSAL.md:16`
    - `docs/PRODUCT_SPEC.md:6`
    - `docs/TASK_BACKLOG.md:5`
  - 위 구간들은 product를 여전히 generic document assistant 수준으로만 압축하고 있어, 이미 shipped된 first reviewed-memory slice를 같은 top-level identity 층위에서 아직 반영하지 않습니다.
- 따라서 latest `/work` 자체는 truthful하지만, same-family closure 주장까지는 그대로 받기 어렵습니다.
- 다음 슬라이스는 `README.md`, `CLAUDE.md`, `PROJECT_CUSTOM_INSTRUCTIONS.md`, `docs/project-brief.md`, `docs/PRODUCT_PROPOSAL.md`, `docs/PRODUCT_SPEC.md`, `docs/TASK_BACKLOG.md`를 함께 묶어 top-level one-line current-identity / status reviewed-memory truth를 맞추는 bounded bundle이 적절합니다.

## 검증
- `sed -n '1,220p' work/4/9/2026-04-09-docs-top-level-current-contract-reviewed-memory-surface-truth-sync.md`
- `sed -n '1,220p' verify/4/9/2026-04-09-docs-current-surface-reviewed-memory-summary-truth-sync-verification.md`
- `git diff --check`
- `git diff -- README.md docs/PRODUCT_SPEC.md docs/ARCHITECTURE.md docs/MILESTONES.md docs/project-brief.md docs/PRODUCT_PROPOSAL.md`
- `nl -ba README.md | sed -n '8,14p'`
- `nl -ba docs/PRODUCT_SPEC.md | sed -n '16,29p'`
- `nl -ba docs/ARCHITECTURE.md | sed -n '9,16p'`
- `nl -ba docs/MILESTONES.md | sed -n '5,12p'`
- `nl -ba docs/project-brief.md | sed -n '13,21p'`
- `nl -ba docs/PRODUCT_PROPOSAL.md | sed -n '24,27p'`
- `rg -n --no-heading 'review queue|검토 후보|검토 메모 적용 후보|reviewed-memory active-effect|reviewed-memory active|first reviewed-memory slice|active-effect path' README.md docs/PRODUCT_SPEC.md docs/ARCHITECTURE.md docs/MILESTONES.md docs/project-brief.md docs/PRODUCT_PROPOSAL.md docs/NEXT_STEPS.md docs/ACCEPTANCE_CRITERIA.md AGENTS.md CLAUDE.md PROJECT_CUSTOM_INSTRUCTIONS.md app/templates/index.html app/handlers/aggregate.py tests/test_web_app.py`
- `rg -n --no-heading 'local-first document assistant web MVP|로컬 퍼스트 문서 비서 웹 MVP|Current Shipped Contract|One-Line Current Product Definition|### Current Product$|### Current Contract$|## Current Product Slice|Current implemented focus:|현재 구현 기준의 중심은 아래입니다\\.|The browser MVP already covers:' README.md AGENTS.md CLAUDE.md PROJECT_CUSTOM_INSTRUCTIONS.md docs/*.md`
- `nl -ba docs/project-brief.md | sed -n '3,8p'`
- `nl -ba docs/PRODUCT_PROPOSAL.md | sed -n '14,18p'`
- `nl -ba README.md | sed -n '1,5p'`
- `nl -ba docs/TASK_BACKLOG.md | sed -n '3,10p'`
- `nl -ba CLAUDE.md | sed -n '1,10p'`
- `nl -ba PROJECT_CUSTOM_INSTRUCTIONS.md | sed -n '1,8p'`
- `nl -ba docs/PRODUCT_SPEC.md | sed -n '1,8p'`
- `nl -ba docs/PRODUCT_PROPOSAL.md | sed -n '1,8p'`
- `rg -n --no-heading 'Current shipped contract: local-first document assistant web MVP|projectH is a \\*\\*local-first document assistant web MVP\\*\\*|This repository is a \\*\\*local-first document assistant web MVP\\*\\*|이 저장소는 \\*\\*로컬 퍼스트 문서 비서 웹 MVP\\*\\*입니다\\.|로컬 퍼스트 문서 비서 웹 MVP' README.md CLAUDE.md PROJECT_CUSTOM_INSTRUCTIONS.md docs/project-brief.md docs/PRODUCT_PROPOSAL.md docs/PRODUCT_SPEC.md`
- Python unit test와 Playwright는 재실행하지 않았습니다. 최신 `/work`가 docs-only이고 code/test/runtime 변경을 주장하지 않았기 때문입니다.

## 남은 리스크
- 최신 `/work`의 직접 수정 대상은 truthful하지만, top-level current-contract reviewed-memory surface family는 one-line identity / status 계층까지는 아직 완전히 닫히지 않았습니다.
- 다음 라운드에서 위 7개 파일의 상단 정의/상태 문구를 함께 맞추면, current shipped contract와 first reviewed-memory slice가 최상단 identity 층위에서도 더 정직하게 정렬됩니다.
