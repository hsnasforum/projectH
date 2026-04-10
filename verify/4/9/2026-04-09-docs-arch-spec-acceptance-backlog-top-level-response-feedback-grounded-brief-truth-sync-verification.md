# docs: arch spec acceptance backlog top-level response-feedback grounded-brief truth sync verification

## 변경 파일
- `verify/4/9/2026-04-09-docs-arch-spec-acceptance-backlog-top-level-response-feedback-grounded-brief-truth-sync-verification.md`
- `.pipeline/claude_handoff.md`

## 사용 skill
- `round-handoff`

## 변경 이유
- 최신 `/work`가 `docs/ARCHITECTURE.md`, `docs/PRODUCT_SPEC.md`, `docs/ACCEPTANCE_CRITERIA.md`, `docs/TASK_BACKLOG.md`의 top-level current-summary wording을 현재 shipped response-feedback / grounded-brief surface와 맞게 정리했는지 다시 확인해야 했습니다.
- direct target과 same-family closure가 truthful하면, 다음은 top-level `next phase` / current-vs-next memory boundary를 한 번에 다시 맞추는 bounded bundle로 넘어가는 편이 더 적절했습니다.

## 핵심 변경
- 최신 `/work`의 직접 수정 대상은 truthful합니다.
  - `docs/ARCHITECTURE.md:10`
  - `docs/PRODUCT_SPEC.md:18`
  - `docs/PRODUCT_SPEC.md:27`
  - `docs/ACCEPTANCE_CRITERIA.md:23`
  - `docs/ACCEPTANCE_CRITERIA.md:24`
  - `docs/TASK_BACKLOG.md:5`
- 현재 문구는 shipped response-feedback / grounded-brief surface와 맞습니다.
  - `README.md:60`
  - `README.md:61`
  - `README.md:62`
  - `README.md:63`
  - `README.md:64`
  - `README.md:65`
  - `docs/PRODUCT_SPEC.md:48`
  - `docs/PRODUCT_SPEC.md:49`
  - `docs/PRODUCT_SPEC.md:50`
  - `docs/PRODUCT_SPEC.md:51`
  - `docs/PRODUCT_SPEC.md:52`
  - `docs/PRODUCT_SPEC.md:62`
  - `docs/PRODUCT_SPEC.md:63`
  - `docs/PRODUCT_SPEC.md:64`
- same-family top-level current-summary response-feedback / grounded-brief drift는 이제 닫힌 것으로 봐도 무방합니다.
  - current-summary headings across root docs and mirrored instruction docs now consistently reflect the shipped surface.
  - `docs/project-brief.md:5`와 `docs/PRODUCT_PROPOSAL.md:16`의 one-line identity 문구는 feature inventory가 아니라 product identity guardrail이라서, 이번 family residual로 보지 않는 판단이 타당합니다.
- 따라서 최신 `/work`의 `남은 리스크 없음`은 이번 family 범위에서는 수용 가능합니다.
- 다음 residual family는 top-level `next phase` / memory-boundary wording입니다.
  - 여전히 아래 구간들이 correction / approval / preference memory를 거의 전부 future layer로만 설명합니다.
    - `README.md:32`
    - `docs/project-brief.md:19`
    - `docs/PRODUCT_PROPOSAL.md:93`
    - `docs/ARCHITECTURE.md:14`
    - `docs/MILESTONES.md:10`
    - `docs/TASK_BACKLOG.md:8`
  - 하지만 current shipped docs와 implementation anchors는 이미 first reviewed-memory / review-queue slice를 현재 계약으로 기록합니다.
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
- 다음 슬라이스는 `README.md`, `docs/project-brief.md`, `docs/PRODUCT_PROPOSAL.md`, `docs/ARCHITECTURE.md`, `docs/MILESTONES.md`, `docs/TASK_BACKLOG.md`를 한 번에 묶어 top-level `next phase` / reviewed-memory boundary truth를 다시 맞추는 bounded bundle이 적절합니다.

## 검증
- `git diff --check`
- `nl -ba docs/ARCHITECTURE.md | sed -n '9,14p'`
- `nl -ba docs/PRODUCT_SPEC.md | sed -n '16,29p'`
- `nl -ba docs/ACCEPTANCE_CRITERIA.md | sed -n '20,32p'`
- `nl -ba docs/TASK_BACKLOG.md | sed -n '3,8p'`
- `git diff -- docs/ARCHITECTURE.md docs/PRODUCT_SPEC.md docs/ACCEPTANCE_CRITERIA.md docs/TASK_BACKLOG.md`
- `rg -n --no-heading 'Current Shipped Contract|Current Product Slice|One-Line Current Product Definition|### Current Contract|### Facts|### Current Product|## Current Checkpoint|## Current Product Identity|Current implemented focus|현재 구현 기준의 중심' README.md docs/*.md AGENTS.md CLAUDE.md PROJECT_CUSTOM_INSTRUCTIONS.md GEMINI.md`
- `rg -n --no-heading 'response feedback capture|응답 피드백 수집|grounded-brief artifact trace anchor|grounded-brief trace anchor|corrected-save bridge|original-response snapshot|artifact-linked reject/reissue reason traces' README.md docs/*.md AGENTS.md CLAUDE.md PROJECT_CUSTOM_INSTRUCTIONS.md GEMINI.md`
- `rg -n --no-heading 'next phase|Next Phase|Next Design Target|Long-Term, Not Current Contract|Long-Term North Star|correction / approval / preference memory|structured correction memory|durable preference memory|review queue|검토 후보|검토 메모 적용' README.md docs/*.md AGENTS.md CLAUDE.md PROJECT_CUSTOM_INSTRUCTIONS.md`
- `nl -ba README.md | sed -n '30,37p'`
- `nl -ba docs/project-brief.md | sed -n '19,22p'`
- `nl -ba docs/PRODUCT_PROPOSAL.md | sed -n '93,100p'`
- `nl -ba docs/ARCHITECTURE.md | sed -n '14,16p'`
- `nl -ba docs/MILESTONES.md | sed -n '10,12p'`
- `nl -ba docs/TASK_BACKLOG.md | sed -n '7,9p'`
- `nl -ba README.md | sed -n '63,70p'`
- `nl -ba docs/PRODUCT_SPEC.md | sed -n '58,64p'`
- `nl -ba docs/PRODUCT_SPEC.md | sed -n '1520,1540p'`
- `nl -ba docs/PRODUCT_SPEC.md | sed -n '1560,1565p'`
- `nl -ba docs/ARCHITECTURE.md | sed -n '29,31p'`
- `nl -ba docs/ARCHITECTURE.md | sed -n '79,80p'`
- `rg -n --no-heading '검토 후보|검토 메모 적용 후보|검토 메모 적용 시작|검토 메모 활성|review_queue_items|recurrence_aggregate_candidates|reviewed_memory_active_effects' app app/frontend tests/test_web_app.py`
- `rg -n --no-heading 'aggregate-transition-apply|future_reviewed_memory_apply|future_reviewed_memory_stop_apply|future_reviewed_memory_reversal|future_reviewed_memory_conflict_visibility' app tests/test_web_app.py`
- Python unit test와 Playwright는 재실행하지 않았습니다. 최신 `/work`가 docs-only이고 code/test/runtime 변경을 주장하지 않았기 때문입니다.

## 남은 리스크
- 최신 `/work`의 직접 수정 대상과 same-family closure 주장은 truthful합니다.
- 다음 남은 drift는 top-level `next phase` / current-vs-next memory boundary wording입니다.
- 다음 라운드에서 위 6개 파일을 함께 맞추면, 현재 already-shipped reviewed-memory / review-queue slice와 아직 future인 broader correction/preference memory를 더 정직하게 분리할 수 있습니다.
