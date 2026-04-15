## 변경 파일

- `verify/4/15/2026-04-15-reviewed-memory-contract-ref-retention-through-lifecycle-parity-bundle-verification.md`
- `.pipeline/claude_handoff.md`

## 사용 skill

- `round-handoff`

## 변경 이유

최신 `/work` 인 `work/4/15/2026-04-15-reviewed-memory-contract-ref-retention-through-lifecycle-parity-bundle.md` 는 `tests/test_web_app.py` 에 contract refs 가 emit/apply/confirm/stop/reverse/conflict visibility 수명주기 전체에서도 contract-only basis ref 로 남는 focused regression 을 추가했고, `python3 -m unittest -v tests.test_smoke tests.test_web_app` 를 green 으로 rerun 했다고 적었습니다. 이번 verify round 에서는 그 claim 이 실제 코드/문서와 재실행 결과에 맞는지 다시 확인하고, 같은 reviewed-memory family 안에서 다음 exact slice 를 다시 좁혔습니다.

또한 프로토콜에 따라 기존 최신 `/verify` 인 `verify/4/15/2026-04-15-reviewed-memory-boundary-draft-apply-separation-parity-bundle-verification.md` 를 먼저 읽고 이어받았습니다.

## 핵심 변경

- `git diff --unified=12 -- tests/test_web_app.py` 와 `sed -n '3666,3898p' tests/test_web_app.py` 확인 결과, `/work` 가 설명한 `test_recurrence_aggregate_contract_refs_retained_through_lifecycle` 메서드는 실제로 존재하고 emit/apply/confirm/stop/reverse/conflict visibility 각 단계에서 `rollback_stage`, `disable_stage`, `conflict_visibility_stage`, `audit_stage`, `post_transition_invariants` 가 유지되며 lifecycle record field 들이 contract surface 로 새지 않는지를 직접 잠급니다.
- `app/serializers.py` 는 여전히 rollback / disable / conflict / transition-audit contract 에 `supporting_source_message_refs`, `supporting_candidate_refs`, optional `supporting_review_refs`, 그리고 contract-only stage 값들을 builder chain 으로 그대로 전달합니다. `app/handlers/aggregate.py` 는 emitted/apply/result/stopped/reversed/conflict records 만 갱신하고 contract refs 자체를 mutate 하지 않습니다. 따라서 `/work` 의 큰 방향, 즉 contract-only surface separation 자체는 현재 구현과 맞습니다.
- Codex 가 focused 신규 테스트를 먼저 rerun 했고 `Ran 1 test in 2.725s`, `OK` 였습니다. 이어 `/work` 가 적은 `python3 -m unittest -v tests.test_smoke tests.test_web_app` 도 다시 실행한 결과 `Ran 370 tests in 118.220s`, `OK` 였습니다. 따라서 이번 `/work` 의 명령 실행 claim 은 현재 truth 와 맞습니다.
- 다만 `/work` 의 `## 핵심 변경` 6번, 즉 "aggregate_identity_ref 및 supporting refs 유지: 모든 contract에서 initial snapshot 과 동일" 설명은 현재 테스트 본문보다 넓습니다. 실제 `assert_contract_refs_unchanged()` 는 rollback contract 에 대해서만 `supporting_source_message_refs` 와 `supporting_candidate_refs` 를 직접 비교하고, disable / conflict / transition-audit contract 에 대해서는 `aggregate_identity_ref` 와 stage/post-transition 값만 비교합니다. optional `supporting_review_refs` 는 어느 contract 에 대해서도 lifecycle 전 단계 직접 비교되지 않습니다. 따라서 최신 `/work` 는 테스트 존재와 재실행 결과 면에서는 truthful 하지만, supporting refs coverage 설명은 과장되어 있습니다.
- 다음 exact slice 는 `reviewed-memory exact supporting-ref lifecycle parity bundle` 로 좁혔습니다. `docs/NEXT_STEPS.md`, `docs/MILESTONES.md`, `docs/TASK_BACKLOG.md`, 그리고 `app/serializers.py` 는 boundary draft 와 rollback/disable/conflict/transition-audit contract 모두가 exact supporting refs 를 유지한다고 정의하고 있습니다. 현재 lifecycle tests 는 boundary draft 와 rollback contract 에서 source/candidate refs 일부만 직접 잠그고 있고, disable / conflict / transition-audit contract 의 exact supporting refs 와 optional `supporting_review_refs` parity 는 아직 직접 잠기지 않았습니다.

## 검증

- `python3 -m unittest -v tests.test_web_app.WebAppServiceTest.test_recurrence_aggregate_contract_refs_retained_through_lifecycle`
  - 결과: `Ran 1 test in 2.725s`, `OK`
- `python3 -m unittest -v tests.test_smoke tests.test_web_app`
  - 결과: `Ran 370 tests in 118.220s`, `OK`
- `git diff --check -- app/serializers.py app/handlers/aggregate.py tests/test_web_app.py docs/NEXT_STEPS.md docs/MILESTONES.md docs/TASK_BACKLOG.md work/4/15`
  - 결과: whitespace 경고 없음
- `git diff --unified=12 -- tests/test_web_app.py`
  - 결과: contract-ref lifecycle parity 테스트 hunk 확인, 동일 파일 내 다른 pending hunk 공존 확인
- `sed -n '3738,3848p' tests/test_web_app.py`
  - 결과: rollback contract 에만 `supporting_source_message_refs` / `supporting_candidate_refs` 직접 비교가 있고, disable / conflict / transition-audit contract 는 현재 `aggregate_identity_ref` 위주로만 확인함을 재확인
- `rg -n "test_recurrence_aggregate_contract_refs_retained_through_lifecycle|contract_only_not_applied|contract_only_not_resolved|contract_only_not_emitted|aggregate_identity_and_contract_refs_retained|rollback_stage|disable_stage|audit_stage|conflict_visibility_stage" tests/test_web_app.py app/serializers.py app/handlers/aggregate.py docs/NEXT_STEPS.md docs/MILESTONES.md docs/TASK_BACKLOG.md`
  - 결과: stage/post-invariant 의 현재 구현/문서 위치 재확인
- `rg -n "supporting_review_refs|supporting_source_message_refs|supporting_candidate_refs" app/serializers.py tests/test_web_app.py`
  - 결과: serializer/document contract 는 exact supporting refs 를 계속 포함하지만, lifecycle parity coverage 는 아직 일부 surface 에 한정됨을 재확인
- `sed -n '1298,1435p' app/serializers.py`
- `sed -n '150,230p' docs/NEXT_STEPS.md`
- `sed -n '446,474p' docs/MILESTONES.md`
- `sed -n '160,210p' docs/TASK_BACKLOG.md`
  - 결과: next priority text 와 serializer contract 는 exact supporting refs 보존을 계속 가리킴
- Playwright / `make e2e-test` 는 rerun 하지 않았습니다. 이번 verify round 는 service/unit contract 와 `/work` claim 재확인에 한정됐고 browser DOM/UI 변경은 없었기 때문입니다.

## 남은 리스크

- 최신 `/work` 는 stage retention / no-leak / rerun command 면에서는 truthful 하지만, supporting refs 가 모든 contract surface 에서 lifecycle 전 단계 동일하다는 설명은 현재 테스트보다 넓습니다.
- 현재 suite 는 boundary draft 와 rollback contract 의 일부 supporting refs parity 는 직접 잠그지만, disable / conflict / transition-audit contract 의 `supporting_source_message_refs`, `supporting_candidate_refs`, optional `supporting_review_refs`, 그리고 boundary draft 의 optional `supporting_review_refs` 는 lifecycle 전 단계 직접 잠그지 않습니다.
- `tests/test_web_app.py` 는 여전히 unrelated pending hunks 를 포함한 dirty 파일입니다. 이번 verify round 는 그것들을 되돌리지 않았고, 최신 `/work` 의 claim 범위와 과장 지점만 truthfully 재대조했습니다.
