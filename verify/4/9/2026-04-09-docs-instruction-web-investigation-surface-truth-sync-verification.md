# docs: instruction web-investigation current-surface truth sync verification

## 변경 파일
- `verify/4/9/2026-04-09-docs-instruction-web-investigation-surface-truth-sync-verification.md`
- `.pipeline/claude_handoff.md`

## 사용 skill
- `round-handoff`

## 변경 이유
- 최신 `/work`가 `AGENTS.md`, `CLAUDE.md`, `PROJECT_CUSTOM_INSTRUCTIONS.md`의 web-investigation current-surface summary를 현재 shipped contract와 맞게 정리했는지 다시 확인해야 했습니다.
- 같은 instruction-doc family가 이번 라운드로 실제로 닫히면, 다음은 같은 family micro-slice가 아니라 남은 current-contract summary residual 하나만 정확히 넘겨야 했습니다.

## 핵심 변경
- 최신 `/work`의 직접 수정 대상은 truthful합니다.
  - `AGENTS.md:43`
  - `AGENTS.md:44`
  - `AGENTS.md:45`
  - `CLAUDE.md:22`
  - `CLAUDE.md:23`
  - `CLAUDE.md:24`
  - `PROJECT_CUSTOM_INSTRUCTIONS.md:20`
  - `PROJECT_CUSTOM_INSTRUCTIONS.md:21`
  - `PROJECT_CUSTOM_INSTRUCTIONS.md:22`
- 현재 문구는 active source-of-truth docs와 맞습니다.
  - instruction docs:
    - `AGENTS.md:43`
    - `CLAUDE.md:22`
    - `PROJECT_CUSTOM_INSTRUCTIONS.md:20`
  - source-of-truth docs:
    - `docs/project-brief.md:15`
    - `docs/project-brief.md:83`
    - `docs/project-brief.md:84`
    - `docs/PRODUCT_PROPOSAL.md:26`
    - `docs/PRODUCT_PROPOSAL.md:63`
    - `docs/PRODUCT_PROPOSAL.md:64`
    - `docs/PRODUCT_PROPOSAL.md:65`
    - `docs/NEXT_STEPS.md:18`
- 따라서 instruction-doc web-investigation current-surface family는 현재 기준으로 닫혔습니다.
  - `AGENTS.md`
  - `CLAUDE.md`
  - `PROJECT_CUSTOM_INSTRUCTIONS.md`
- 최신 `/work`의 `GEMINI.md에 동일 패턴 잔여 가능` 메모는 현재 residual로 승격할 필요가 없습니다.
  - `GEMINI.md`는 current product/current contract bullet 문서가 아니라 arbitration-role 문서입니다.
- 다음 residual은 instruction docs가 아니라 `docs/ARCHITECTURE.md` 내부의 current-contract / web-investigation summary wording입니다.
  - `docs/ARCHITECTURE.md:11`
  - `docs/ARCHITECTURE.md:125`
  - `docs/ARCHITECTURE.md:130`
  - `docs/ARCHITECTURE.md:131`
  - `docs/ARCHITECTURE.md:1364`
- 이 구간은 아직 `response renders source roles and claim coverage state`, `search history is stored locally`, `claim coverage state and reinvestigation helpers`처럼 더 압축된 표현에 머물러 있어, 현재 shipped detail인 history-card badges, entity-card/latest-update distinction, entity-card strong-badge downgrade, dedicated plain-language focus-slot reinvestigation explanation보다 좁습니다.
  - `docs/PRODUCT_SPEC.md:153`
  - `docs/PRODUCT_SPEC.md:154`
  - `docs/PRODUCT_SPEC.md:155`
  - `docs/PRODUCT_SPEC.md:358`
  - `docs/PRODUCT_SPEC.md:359`
  - `docs/PRODUCT_SPEC.md:360`
  - `docs/PRODUCT_SPEC.md:361`

## 검증
- `git diff --check`
- `nl -ba CLAUDE.md | sed -n '20,26p'`
- `nl -ba PROJECT_CUSTOM_INSTRUCTIONS.md | sed -n '18,24p'`
- `git diff -- AGENTS.md CLAUDE.md PROJECT_CUSTOM_INSTRUCTIONS.md`
- `rg -n --no-heading 'disabled/approval/enabled per session|history-card badges|entity-card / latest-update|claim-coverage panel|focus-slot reinvestigation' AGENTS.md CLAUDE.md PROJECT_CUSTOM_INSTRUCTIONS.md docs/project-brief.md docs/PRODUCT_PROPOSAL.md docs/NEXT_STEPS.md`
- `nl -ba docs/project-brief.md | sed -n '13,16p;81,84p'`
- `nl -ba docs/PRODUCT_PROPOSAL.md | sed -n '24,27p;61,65p'`
- `nl -ba docs/NEXT_STEPS.md | sed -n '16,18p'`
- `nl -ba docs/ARCHITECTURE.md | sed -n '125,132p;1360,1365p'`
- `nl -ba docs/PRODUCT_SPEC.md | sed -n '152,156p;357,361p'`
- Python unit test와 Playwright는 재실행하지 않았습니다. 최신 `/work`가 docs-only이고 code/test/runtime 변경을 주장하지 않았기 때문입니다.

## 남은 리스크
- 최신 `/work`의 직접 수정 대상은 truthful합니다.
- instruction-doc web-investigation current-surface family는 닫혔습니다.
- 다만 `docs/ARCHITECTURE.md`의 current-contract / web-investigation summary는 여전히 shipped detail보다 축약돼 있으므로, 다음 라운드에서 한 파일로 정리하는 편이 적절합니다.
