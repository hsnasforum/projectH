# docs: architecture web-investigation current-contract summary truth sync verification

## 변경 파일
- `verify/4/9/2026-04-09-docs-architecture-web-investigation-contract-summary-truth-sync-verification.md`
- `.pipeline/claude_handoff.md`

## 사용 skill
- `round-handoff`

## 변경 이유
- 최신 `/work`가 `docs/ARCHITECTURE.md`의 web-investigation current-contract summary를 현재 shipped contract와 맞게 정리했는지 다시 확인해야 했습니다.
- 같은 web-investigation docs family가 이번 라운드에서 실제로 닫히지 않았다면, 다음은 한 개의 남은 current-contract summary bundle만 넘겨야 했습니다.

## 핵심 변경
- 최신 `/work`의 직접 수정 대상은 truthful합니다.
  - `docs/ARCHITECTURE.md:11`
  - `docs/ARCHITECTURE.md:130`
  - `docs/ARCHITECTURE.md:131`
  - `docs/ARCHITECTURE.md:132`
  - `docs/ARCHITECTURE.md:1365`
  - `docs/ARCHITECTURE.md:1366`
  - `docs/ARCHITECTURE.md:1367`
- 현재 문구는 shipped truth와 맞습니다.
  - `docs/ARCHITECTURE.md:11`은 permission-gated secondary mode, disabled/approval/enabled per session, history-card badges, entity-card / latest-update distinction, strong-badge downgrade, claim-coverage panel detail을 모두 반영합니다.
  - `docs/ARCHITECTURE.md:130`
  - `docs/ARCHITECTURE.md:131`
  - `docs/ARCHITECTURE.md:132`
  - `docs/ARCHITECTURE.md:1365`
  - `docs/ARCHITECTURE.md:1366`
  - `docs/ARCHITECTURE.md:1367`
  - 근거 source-of-truth:
    - `docs/PRODUCT_SPEC.md:153`
    - `docs/PRODUCT_SPEC.md:154`
    - `docs/PRODUCT_SPEC.md:155`
    - `docs/PRODUCT_SPEC.md:358`
    - `docs/PRODUCT_SPEC.md:359`
    - `docs/PRODUCT_SPEC.md:360`
    - `docs/PRODUCT_SPEC.md:361`
- 다만 최신 `/work`의 `남은 리스크 없음`은 과합니다.
  - 같은 current-contract summary family residual이 top-level docs에 남아 있습니다.
    - `docs/project-brief.md:15`
    - `docs/project-brief.md:16`
    - `docs/PRODUCT_PROPOSAL.md:26`
    - `docs/PRODUCT_PROPOSAL.md:69`
- 이 구간은 web investigation을 secondary mode로 적는 큰 방향은 맞지만, 아래 same-file detail이나 이미 synced source-of-truth docs가 적는 shipped surface보다 여전히 축약돼 있습니다.
  - `docs/project-brief.md:83`
  - `docs/project-brief.md:84`
  - `docs/project-brief.md:85`
  - `docs/PRODUCT_PROPOSAL.md:63`
  - `docs/PRODUCT_PROPOSAL.md:64`
  - `docs/PRODUCT_PROPOSAL.md:65`
- 따라서 `docs/ARCHITECTURE.md` 라운드 자체는 truthful하지만, current-contract web-investigation summary family 전체 기준으로는 아직 닫히지 않았습니다.
- 다음 슬라이스는 `docs/project-brief.md`, `docs/PRODUCT_PROPOSAL.md` 두 파일의 top-level current-contract/facts summary를 한 번에 맞추는 bounded bundle이 적절합니다.

## 검증
- `git diff --check`
- `nl -ba docs/ARCHITECTURE.md | sed -n '9,16p;125,133p;1360,1367p'`
- `git diff -- docs/ARCHITECTURE.md`
- `rg -n --no-heading 'history-card|entity-card / latest-update|claim coverage|focus-slot reinvestigation|strong-badge downgrade|secondary mode|disabled/approval/enabled per session' docs/ARCHITECTURE.md docs/PRODUCT_SPEC.md docs/NEXT_STEPS.md docs/project-brief.md docs/PRODUCT_PROPOSAL.md`
- `nl -ba docs/PRODUCT_SPEC.md | sed -n '152,156p;357,361p'`
- `nl -ba docs/project-brief.md | sed -n '13,18p;83,85p'`
- `nl -ba docs/PRODUCT_PROPOSAL.md | sed -n '24,27p;39,48p;63,65p;67,69p'`
- Python unit test와 Playwright는 재실행하지 않았습니다. 최신 `/work`가 docs-only이고 code/test/runtime 변경을 주장하지 않았기 때문입니다.

## 남은 리스크
- 최신 `/work`의 직접 수정 대상은 truthful합니다.
- 다만 current-contract web-investigation summary family는 아직 `docs/project-brief.md`, `docs/PRODUCT_PROPOSAL.md`의 top-level summary residual 때문에 완전히 닫히지 않았습니다.
- 다음 라운드에서 두 파일을 한 묶음으로 맞추면 이 family는 current-contract top-level 기준으로 닫힐 가능성이 높습니다.
