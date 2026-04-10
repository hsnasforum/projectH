# docs: instruction response-feedback grounded-brief surface truth sync verification

## 변경 파일
- `verify/4/9/2026-04-09-docs-instruction-response-feedback-grounded-brief-surface-truth-sync-verification.md`
- `.pipeline/claude_handoff.md`

## 사용 skill
- `round-handoff`

## 변경 이유
- 최신 `/work`가 `AGENTS.md`, `CLAUDE.md`, `PROJECT_CUSTOM_INSTRUCTIONS.md`의 current product slice summary를 현재 shipped response-feedback / grounded-brief surface와 맞게 정리했는지 다시 확인해야 했습니다.
- direct target이 truthful하면, 다음은 더 작은 instruction-doc micro-slice가 아니라 root docs top-level current-summary family를 한 번에 정리하는 쪽이 더 적절했습니다.

## 핵심 변경
- 최신 `/work`의 직접 수정 대상은 truthful합니다.
  - `AGENTS.md:42`
  - `AGENTS.md:43`
  - `CLAUDE.md:21`
  - `CLAUDE.md:22`
  - `PROJECT_CUSTOM_INSTRUCTIONS.md:19`
  - `PROJECT_CUSTOM_INSTRUCTIONS.md:20`
- 현재 문구는 shipped response-feedback / grounded-brief surface와 맞습니다.
  - `README.md:57`
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
  - `docs/PRODUCT_SPEC.md:62`
  - `docs/PRODUCT_SPEC.md:63`
  - `docs/PRODUCT_SPEC.md:64`
- 따라서 instruction-doc current product slice family에서 response-feedback / grounded-brief omission은 이번 라운드로 닫힌 것으로 봐도 무방합니다.
- 다만 최신 `/work`의 `남은 리스크 없음`은 과합니다.
  - 같은 current-summary family의 root docs top-level wording이 아직 shipped surface를 충분히 반영하지 않습니다.
    - `README.md:8`
    - `README.md:42`
    - `docs/project-brief.md:15`
    - `docs/PRODUCT_PROPOSAL.md:25`
    - `docs/MILESTONES.md:6`
    - `docs/NEXT_STEPS.md:5`
  - 위 구간들은 current product summary에서 web-investigation secondary mode까지는 적고 있지만, response feedback capture와 grounded-brief trace / corrected-outcome / corrected-save surface는 누락하거나 지나치게 압축하고 있습니다.
- 다음 슬라이스는 `README.md`, `docs/project-brief.md`, `docs/PRODUCT_PROPOSAL.md`, `docs/MILESTONES.md`, `docs/NEXT_STEPS.md`를 한 번에 묶어 top-level current-summary wording을 현재 shipped surface와 맞추는 bounded bundle이 적절합니다.

## 검증
- `git diff --check`
- `nl -ba AGENTS.md | sed -n '29,47p'`
- `nl -ba CLAUDE.md | sed -n '9,27p'`
- `nl -ba PROJECT_CUSTOM_INSTRUCTIONS.md | sed -n '6,24p'`
- `git diff -- AGENTS.md CLAUDE.md PROJECT_CUSTOM_INSTRUCTIONS.md`
- `nl -ba README.md | sed -n '57,62p'`
- `nl -ba docs/PRODUCT_SPEC.md | sed -n '48,64p'`
- `rg -n --no-heading 'response feedback capture|응답 피드백 수집|grounded-brief artifact trace anchor|original-response snapshot|corrected-outcome capture|corrected-save bridge|reject/reissue reason traces' AGENTS.md CLAUDE.md PROJECT_CUSTOM_INSTRUCTIONS.md GEMINI.md README.md docs/PRODUCT_SPEC.md`
- `nl -ba README.md | sed -n '8,12p'`
- `nl -ba README.md | sed -n '42,43p'`
- `nl -ba docs/project-brief.md | sed -n '13,16p'`
- `nl -ba docs/PRODUCT_PROPOSAL.md | sed -n '24,27p'`
- `nl -ba docs/MILESTONES.md | sed -n '5,8p'`
- `nl -ba docs/NEXT_STEPS.md | sed -n '5,18p'`
- `rg -n --no-heading 'Current Contract|Current Product|Current Checkpoint|Current Shipped Contract|### Facts|current shipped behavior|현재 구현된 웹 MVP|현재 구현 기준의 중심' README.md docs/project-brief.md docs/PRODUCT_PROPOSAL.md docs/ARCHITECTURE.md docs/MILESTONES.md docs/NEXT_STEPS.md`
- `rg -n --no-heading 'response feedback capture|grounded-brief trace|corrected-save|original-response snapshot|approval_reason_record|content_reason_record' README.md docs/project-brief.md docs/PRODUCT_PROPOSAL.md docs/ARCHITECTURE.md docs/MILESTONES.md docs/NEXT_STEPS.md`
- Python unit test와 Playwright는 재실행하지 않았습니다. 최신 `/work`가 docs-only이고 code/test/runtime 변경을 주장하지 않았기 때문입니다.

## 남은 리스크
- 최신 `/work`의 직접 수정 대상은 truthful합니다.
- 다만 same-day docs 전체 기준으로는 root docs top-level current-summary family residual이 아직 남아 있습니다.
- 다음 라운드에서 `README.md`, `docs/project-brief.md`, `docs/PRODUCT_PROPOSAL.md`, `docs/MILESTONES.md`, `docs/NEXT_STEPS.md`를 함께 맞추면, current product summary가 response-feedback / grounded-brief correction surface를 더 정직하게 반영하게 됩니다.
