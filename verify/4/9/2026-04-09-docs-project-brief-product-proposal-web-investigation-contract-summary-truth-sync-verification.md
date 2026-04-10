# docs: project-brief product-proposal web-investigation current-contract summary truth sync verification

## 변경 파일
- `verify/4/9/2026-04-09-docs-project-brief-product-proposal-web-investigation-contract-summary-truth-sync-verification.md`
- `.pipeline/claude_handoff.md`

## 사용 skill
- `round-handoff`

## 변경 이유
- 최신 `/work`가 `docs/project-brief.md`, `docs/PRODUCT_PROPOSAL.md`의 top-level web-investigation current-contract summary를 현재 shipped truth와 맞게 정리했는지 다시 확인해야 했습니다.
- direct target이 truthful하면, 다음은 더 작은 web-investigation micro-slice가 아니라 현재 shipped grounded-brief current-vs-next drift 같은 새 docs axis로 넘어가야 했습니다.

## 핵심 변경
- 최신 `/work`의 직접 수정 대상은 truthful합니다.
  - `docs/project-brief.md:15`
  - `docs/PRODUCT_PROPOSAL.md:26`
- 현재 문구는 shipped truth와 맞습니다.
  - `docs/project-brief.md:15`
  - `docs/PRODUCT_PROPOSAL.md:26`
  - source-of-truth anchors:
    - `docs/ARCHITECTURE.md:11`
    - `docs/PRODUCT_SPEC.md:153`
    - `docs/PRODUCT_SPEC.md:154`
    - `docs/PRODUCT_SPEC.md:155`
    - `docs/PRODUCT_SPEC.md:358`
    - `docs/PRODUCT_SPEC.md:360`
    - `docs/PRODUCT_SPEC.md:361`
    - `docs/NEXT_STEPS.md:18`
- `docs/PRODUCT_PROPOSAL.md:69` boundary line을 그대로 둔 판단도 현재 scope에서는 타당합니다.
  - 이 줄은 shipped surface detail이 아니라 `secondary mode` boundary만 요약하는 top-level guardrail 문구이기 때문입니다.
- 다만 최신 `/work`의 `남은 리스크 없음`은 과합니다.
  - 다른 docs family residual이 아직 남아 있습니다.
    - `docs/project-brief.md:91`
    - `docs/PRODUCT_PROPOSAL.md:144`
    - `docs/PRODUCT_PROPOSAL.md:145`
    - `docs/PRODUCT_PROPOSAL.md:147`
- 현재 shipped truth는 이미 grounded-brief trace/correction foundation을 포함합니다.
  - `README.md:58`
  - `README.md:59`
  - `README.md:60`
  - `README.md:61`
  - `README.md:62`
  - `docs/PRODUCT_SPEC.md:48`
  - `docs/PRODUCT_SPEC.md:49`
  - `docs/PRODUCT_SPEC.md:50`
  - `docs/PRODUCT_SPEC.md:51`
  - `docs/PRODUCT_SPEC.md:52`
  - `docs/PRODUCT_SPEC.md:53`
  - `docs/PRODUCT_SPEC.md:62`
  - `docs/PRODUCT_SPEC.md:63`
  - `docs/PRODUCT_SPEC.md:64`
  - `docs/PRODUCT_SPEC.md:301`
  - `docs/PRODUCT_SPEC.md:524`
  - `docs/PRODUCT_SPEC.md:558`
  - `docs/PRODUCT_SPEC.md:559`
  - `docs/PRODUCT_SPEC.md:648`
- 반면 residual lines는 아직 이를 later/needed-next로 적고 있어 current-vs-next truth가 어긋납니다.
  - `docs/project-brief.md:91`의 ``grounded brief` artifact identity`
  - `docs/PRODUCT_PROPOSAL.md:144`의 `grounded-brief artifact snapshots`
  - `docs/PRODUCT_PROPOSAL.md:145`의 `corrected output pairs`
  - `docs/PRODUCT_PROPOSAL.md:147`의 `artifact-linked rejection reasons`
- 따라서 latest `/work` 자체는 truthful하지만, same-day docs 전체 기준으로는 새로운 grounded-brief current-vs-next family residual이 남아 있습니다.
- 다음 슬라이스는 `docs/project-brief.md`, `docs/PRODUCT_PROPOSAL.md`를 한 번에 묶어 grounded-brief trace/correction foundation의 현재 shipped 범위와 아직 next인 correction-memory schema / durable preference layer를 다시 나누는 bounded bundle이 적절합니다.

## 검증
- `git diff --check`
- `nl -ba docs/project-brief.md | sed -n '13,18p;83,85p;88,92p'`
- `nl -ba docs/PRODUCT_PROPOSAL.md | sed -n '24,27p;63,65p;67,69p;96,104p;133,147p'`
- `git diff -- docs/project-brief.md docs/PRODUCT_PROPOSAL.md`
- `rg -n --no-heading 'history-card badges|entity-card / latest-update|strong-badge downgrade|claim-coverage panel|secondary mode|disabled/approval/enabled per session' docs/project-brief.md docs/PRODUCT_PROPOSAL.md docs/ARCHITECTURE.md docs/PRODUCT_SPEC.md docs/NEXT_STEPS.md README.md`
- `rg -n --no-heading '`grounded brief` artifact identity|grounded-brief artifact snapshots|corrected output pairs|artifact-linked rejection reasons' docs/project-brief.md docs/PRODUCT_PROPOSAL.md`
- `rg -n --no-heading 'content_reason_record|approval_reason_record|corrected_text persistence|corrected-outcome capture|artifact_id|source_message_id|save_content_source = original_draft \\| corrected_text' README.md docs/PRODUCT_SPEC.md`
- `nl -ba README.md | sed -n '57,63p'`
- `nl -ba docs/PRODUCT_SPEC.md | sed -n '48,64p;300,305p;520,525p;552,564p;648,664p'`
- Python unit test와 Playwright는 재실행하지 않았습니다. 최신 `/work`가 docs-only이고 code/test/runtime 변경을 주장하지 않았기 때문입니다.

## 남은 리스크
- 최신 `/work`의 직접 수정 대상은 truthful합니다.
- 다만 `남은 리스크 없음`은 그대로 수용하기 어렵습니다. same-day docs family 기준으로 `project-brief` / `PRODUCT_PROPOSAL`의 grounded-brief current-vs-next residual이 아직 남아 있습니다.
- 다음 라운드에서 두 파일을 한 묶음으로 맞추면, current shipped trace foundation과 아직 next인 structured correction-memory / durable preference layer의 경계가 더 정직해집니다.
