# docs: project-brief product-proposal grounded-brief current-vs-next truth sync verification

## 변경 파일
- `verify/4/9/2026-04-09-docs-project-brief-product-proposal-grounded-brief-current-vs-next-truth-sync-verification.md`
- `.pipeline/claude_handoff.md`

## 사용 skill
- `round-handoff`

## 변경 이유
- 최신 `/work`가 `docs/project-brief.md`, `docs/PRODUCT_PROPOSAL.md`의 grounded-brief current-vs-next wording을 현재 shipped truth와 맞게 정리했는지 다시 확인해야 했습니다.
- direct target이 truthful하면, 다음은 같은 두 파일을 더 쪼개는 대신 mirrored instruction docs의 current product slice omission을 한 번에 정리하는 쪽이 더 적절했습니다.

## 핵심 변경
- 최신 `/work`의 직접 수정 대상은 truthful합니다.
  - `docs/project-brief.md:88`
  - `docs/PRODUCT_PROPOSAL.md:143`
- 현재 문구는 shipped grounded-brief trace/correction foundation과 맞습니다.
  - `docs/project-brief.md:89`
  - `docs/project-brief.md:90`
  - `docs/project-brief.md:91`
  - `docs/project-brief.md:92`
  - `docs/project-brief.md:97`
  - `docs/PRODUCT_PROPOSAL.md:144`
  - `docs/PRODUCT_PROPOSAL.md:145`
  - `docs/PRODUCT_PROPOSAL.md:146`
  - `docs/PRODUCT_PROPOSAL.md:147`
  - `docs/PRODUCT_PROPOSAL.md:150`
  - `docs/PRODUCT_PROPOSAL.md:151`
  - source-of-truth anchors:
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
    - `docs/PRODUCT_SPEC.md:303`
    - `docs/PRODUCT_SPEC.md:556`
    - `docs/PRODUCT_SPEC.md:558`
    - `docs/PRODUCT_SPEC.md:559`
    - `docs/PRODUCT_SPEC.md:648`
    - `docs/PRODUCT_SPEC.md:650`
    - `docs/PRODUCT_SPEC.md:653`
- 따라서 `project-brief` / `PRODUCT_PROPOSAL`의 grounded-brief current-vs-next family는 이번 라운드로 닫힌 것으로 봐도 무방합니다.
- 다만 최신 `/work`의 `남은 리스크 없음`은 과합니다.
  - mirrored instruction docs의 current product slice summary는 아직 shipped response-feedback / grounded-brief surface를 빠뜨리고 있습니다.
    - `AGENTS.md:29`
    - `CLAUDE.md:9`
    - `PROJECT_CUSTOM_INSTRUCTIONS.md:6`
  - 위 세 문서는 current product slice에 web-investigation surface까지는 반영했지만, 아직 response feedback capture와 grounded-brief trace/correction/corrected-save surface는 요약하지 않습니다.
- 다음 슬라이스는 `AGENTS.md`, `CLAUDE.md`, `PROJECT_CUSTOM_INSTRUCTIONS.md`를 한 번에 묶어 current product slice summary를 현재 shipped surface와 맞추는 bounded bundle이 적절합니다.

## 검증
- `git diff --check`
- `nl -ba docs/project-brief.md | sed -n '86,96p'`
- `nl -ba docs/PRODUCT_PROPOSAL.md | sed -n '136,151p'`
- `git diff -- docs/project-brief.md docs/PRODUCT_PROPOSAL.md`
- `nl -ba README.md | sed -n '56,63p'`
- `nl -ba docs/PRODUCT_SPEC.md | sed -n '48,64p'`
- `nl -ba docs/PRODUCT_SPEC.md | sed -n '300,305p'`
- `nl -ba docs/PRODUCT_SPEC.md | sed -n '552,564p'`
- `nl -ba docs/PRODUCT_SPEC.md | sed -n '648,664p'`
- `rg -n --no-heading -C 2 'grounded-brief artifact|grounded brief artifact|original-response snapshot|corrected-outcome capture|reject / reissue reason|corrected-save linkage|structured correction-memory schema|durable preference-rule candidates' README.md docs/*.md`
- `nl -ba README.md | sed -n '16,24p'`
- `nl -ba AGENTS.md | sed -n '29,44p'`
- `nl -ba CLAUDE.md | sed -n '1,24p'`
- `nl -ba PROJECT_CUSTOM_INSTRUCTIONS.md | sed -n '1,24p'`
- `rg -n --no-heading 'response feedback capture|grounded-brief artifact trace|correction editor|corrected-save|save_content_source|source_message_id|내용 거절|content_reason_record|approval_reason_record' README.md AGENTS.md CLAUDE.md PROJECT_CUSTOM_INSTRUCTIONS.md docs/project-brief.md docs/PRODUCT_PROPOSAL.md`
- Python unit test와 Playwright는 재실행하지 않았습니다. 최신 `/work`가 docs-only이고 code/test/runtime 변경을 주장하지 않았기 때문입니다.

## 남은 리스크
- 최신 `/work`의 직접 수정 대상은 truthful합니다.
- 다만 same-day docs 전체 기준으로는 instruction docs current product slice omission이 아직 남아 있습니다.
- 다음 라운드에서 `AGENTS.md`, `CLAUDE.md`, `PROJECT_CUSTOM_INSTRUCTIONS.md`를 함께 맞추면, current product slice가 현재 shipped response-feedback / grounded-brief surface를 더 정직하게 요약하게 됩니다.
