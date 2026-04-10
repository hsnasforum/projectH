## 변경 파일
- `verify/4/9/2026-04-09-docs-aggregate-item-capability-basis-conditional-truth-sync-verification.md`
- `.pipeline/claude_handoff.md`

## 사용 skill
- `round-handoff`

## 변경 이유
- 최신 Claude `/work`인 `work/4/9/2026-04-09-docs-aggregate-item-capability-basis-conditional-truth-sync.md`의 주장이 현재 문서 truth와 맞는지 다시 확인했습니다.
- 같은 날 최신 `/verify`인 `verify/4/9/2026-04-09-docs-aggregate-item-overview-projection-vs-record-truth-sync-verification.md`를 이어서 읽고 같은 recurrence-aggregate item family의 후속 current-risk reduction을 한 줄로 다시 좁혔습니다.

## 핵심 변경
- 최신 `/work`가 고친 `docs/PRODUCT_SPEC.md:61`, `docs/PRODUCT_SPEC.md:229`, `docs/ARCHITECTURE.md:78`, `docs/ARCHITECTURE.md:190`, `docs/ACCEPTANCE_CRITERIA.md:111` 의 `reviewed_memory_capability_basis` conditional wording은 현재 shipped truth와 맞습니다. 현재 root overview는 `reviewed_memory_capability_basis`를 `capability_outcome = unblocked_all_required`일 때만 present한 conditional field로 적고 있고, 이는 `app/serializers.py:3691-3702`, `app/serializers.py:1504-1517`, `tests/test_smoke.py:5818-5833` 와 일치합니다.
- 이번 `/work` closeout의 `남은 리스크 없음` 판단도 해당 root-overview 5줄 범위에서는 과장으로 보지 않았습니다.
- 다음 same-family current-risk reduction은 planning docs의 aggregate item contract-object wording입니다. `docs/NEXT_STEPS.md:122`, `docs/NEXT_STEPS.md:146`, `docs/NEXT_STEPS.md:156`, `docs/NEXT_STEPS.md:166`, `docs/NEXT_STEPS.md:177`, `docs/NEXT_STEPS.md:189` 과 `docs/TASK_BACKLOG.md:145`, `docs/TASK_BACKLOG.md:146`, `docs/TASK_BACKLOG.md:336`, `docs/TASK_BACKLOG.md:367`, `docs/TASK_BACKLOG.md:397`, `docs/TASK_BACKLOG.md:425`, `docs/TASK_BACKLOG.md:456` 은 아직 `may now also expose` / `can now also expose` 로 적지만, 대응 wording은 `docs/MILESTONES.md:200`, `docs/MILESTONES.md:204`, `docs/MILESTONES.md:216`, `docs/MILESTONES.md:228`, `docs/MILESTONES.md:242`, `docs/MILESTONES.md:259` 와 root docs에서 이미 current shipped로 잠겨 있습니다.
- 다음 Claude 슬라이스는 `.pipeline/claude_handoff.md`에 `Docs NEXT_STEPS TASK_BACKLOG recurrence aggregate item contract-object current-shipped wording truth sync`로 고정했습니다.

## 검증
- `sed -n '1,220p' .agents/skills/round-handoff/SKILL.md`
- `sed -n '1,220p' AGENTS.md`
- `sed -n '1,220p' work/README.md`
- `sed -n '1,220p' verify/README.md`
- `sed -n '1,220p' .pipeline/README.md`
- `sed -n '1,220p' work/4/9/2026-04-09-docs-aggregate-item-capability-basis-conditional-truth-sync.md`
- `sed -n '1,220p' verify/4/9/2026-04-09-docs-aggregate-item-overview-projection-vs-record-truth-sync-verification.md`
- `nl -ba docs/PRODUCT_SPEC.md | sed -n '58,62p'`
- `nl -ba docs/PRODUCT_SPEC.md | sed -n '226,231p'`
- `nl -ba docs/ARCHITECTURE.md | sed -n '76,80p'`
- `nl -ba docs/ARCHITECTURE.md | sed -n '188,191p'`
- `nl -ba docs/ACCEPTANCE_CRITERIA.md | sed -n '108,112p'`
- `nl -ba app/serializers.py | sed -n '1045,1490p'`
- `rg -n 'capability_basis|planning_target_ref|blocked_all_required|unblocked_all_required' docs/MILESTONES.md docs/NEXT_STEPS.md docs/TASK_BACKLOG.md -S`
- `nl -ba docs/MILESTONES.md | sed -n '190,260p'`
- `nl -ba docs/NEXT_STEPS.md | sed -n '118,190p'`
- `nl -ba docs/TASK_BACKLOG.md | sed -n '332,458p'`
- `git diff --check`

## 남은 리스크
- `docs/NEXT_STEPS.md:122`, `docs/NEXT_STEPS.md:146`, `docs/NEXT_STEPS.md:156`, `docs/NEXT_STEPS.md:166`, `docs/NEXT_STEPS.md:177`, `docs/NEXT_STEPS.md:189` 과 `docs/TASK_BACKLOG.md:145`, `docs/TASK_BACKLOG.md:146`, `docs/TASK_BACKLOG.md:336`, `docs/TASK_BACKLOG.md:367`, `docs/TASK_BACKLOG.md:397`, `docs/TASK_BACKLOG.md:425`, `docs/TASK_BACKLOG.md:456` 은 아직 aggregate item contract-object를 current shipped보다 약한 `may/can now expose` phrasing으로 남기고 있습니다.
- 이번 라운드는 docs/code truth 대조와 `git diff --check`만 다시 확인했습니다.
- Python unit test와 Playwright는 재실행하지 않았습니다.
