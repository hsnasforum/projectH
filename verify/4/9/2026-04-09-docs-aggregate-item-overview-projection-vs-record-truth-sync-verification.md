## 변경 파일
- `verify/4/9/2026-04-09-docs-aggregate-item-overview-projection-vs-record-truth-sync-verification.md`
- `.pipeline/claude_handoff.md`

## 사용 skill
- `round-handoff`

## 변경 이유
- 최신 Claude `/work`인 `work/4/9/2026-04-09-docs-aggregate-item-overview-projection-vs-record-truth-sync.md`의 주장이 현재 문서 truth와 맞는지 다시 확인했습니다.
- 같은 날 최신 `/verify`인 `verify/4/9/2026-04-09-docs-acceptance-capability-basis-shipped-truth-sync-verification.md`를 이어서 읽고 같은 recurrence-aggregate item family의 후속 current-risk reduction을 한 줄로 다시 좁혔습니다.

## 핵심 변경
- 최신 `/work`가 고친 `docs/PRODUCT_SPEC.md:61`, `docs/PRODUCT_SPEC.md:229`, `docs/ARCHITECTURE.md:78`, `docs/ARCHITECTURE.md:190`, `docs/ACCEPTANCE_CRITERIA.md:111`의 projection-vs-record 분리 방향 자체는 현재 serializer 구조와 맞습니다. `reviewed_memory_transition_record`를 conditional lifecycle record로, `reviewed_memory_conflict_visibility_record`를 optional lifecycle record로 뺀 부분은 truthful합니다.
- 다만 같은 줄들이 `reviewed_memory_capability_basis`까지 deterministic read-only projection으로 묶은 것은 현재 shipped truth와 어긋납니다. 실제 구현은 `app/serializers.py:3691-3702`에서 `reviewed_memory_capability_basis`를 full capability-source family와 matching unblock-contract가 있을 때만 만들고, `app/serializers.py:1504-1517`는 basis가 없으면 `reviewed_memory_capability_status.capability_outcome = blocked_all_required`를 유지합니다.
- 테스트도 이 conditional truth를 잠급니다. `tests/test_smoke.py:5818-5833`는 serialized aggregate에 `reviewed_memory_capability_basis`가 없으면서 `reviewed_memory_planning_target_ref`는 남는 경우를 확인하고, `tests/test_smoke.py:5901-5905`는 그 same blocked/support-only path에서 capability status가 계속 계산됨을 확인합니다.
- 따라서 이번 `/work` closeout의 `남은 리스크 없음 — aggregate item 개요의 projection vs record 구분 진실 동기화 완료` 판단은 과합니다. root overview family는 아직 `reviewed_memory_capability_basis`의 conditional presence를 직접 닫지 못했습니다.
- 다음 Claude 슬라이스는 `.pipeline/claude_handoff.md`에 `Docs PRODUCT_SPEC ARCHITECTURE ACCEPTANCE_CRITERIA recurrence aggregate item overview capability-basis conditional wording truth sync`로 고정했습니다.

## 검증
- `sed -n '1,220p' work/4/9/2026-04-09-docs-aggregate-item-overview-projection-vs-record-truth-sync.md`
- `sed -n '1,220p' verify/4/9/2026-04-09-docs-acceptance-capability-basis-shipped-truth-sync-verification.md`
- `sed -n '1,220p' .agents/skills/round-handoff/SKILL.md`
- `sed -n '1,220p' AGENTS.md`
- `sed -n '1,220p' work/README.md`
- `sed -n '1,220p' verify/README.md`
- `sed -n '1,220p' .pipeline/README.md`
- `nl -ba docs/PRODUCT_SPEC.md | sed -n '58,62p'`
- `nl -ba docs/PRODUCT_SPEC.md | sed -n '226,231p'`
- `nl -ba docs/ARCHITECTURE.md | sed -n '76,80p'`
- `nl -ba docs/ARCHITECTURE.md | sed -n '188,191p'`
- `nl -ba docs/ACCEPTANCE_CRITERIA.md | sed -n '108,112p'`
- `rg -n 'reviewed_memory_capability_basis|blocked_all_required|unblocked_all_required|planning_target_ref|deterministic read-only projections' docs/PRODUCT_SPEC.md docs/ARCHITECTURE.md docs/ACCEPTANCE_CRITERIA.md -S`
- `nl -ba app/serializers.py | sed -n '1480,1518p'`
- `nl -ba app/serializers.py | sed -n '3691,3749p'`
- `nl -ba tests/test_smoke.py | sed -n '5818,5834p'`
- `nl -ba tests/test_smoke.py | sed -n '5896,5905p'`
- `git diff --check`

## 남은 리스크
- `docs/PRODUCT_SPEC.md:61`, `docs/PRODUCT_SPEC.md:229`, `docs/ARCHITECTURE.md:78`, `docs/ARCHITECTURE.md:190`, `docs/ACCEPTANCE_CRITERIA.md:111` 은 아직 `reviewed_memory_capability_basis`를 deterministic projection처럼 읽히게 만듭니다.
- 이번 라운드는 docs/code truth 대조와 `git diff --check`만 다시 확인했습니다.
- Python unit test와 Playwright는 재실행하지 않았습니다.
