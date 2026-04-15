## 변경 파일

- `verify/4/15/2026-04-15-reviewed-memory-precondition-status-blocked-only-parity-bundle-verification.md`
- `.pipeline/claude_handoff.md`

## 사용 skill

- `round-handoff`

## 변경 이유

최신 `/work` 가 `tests/test_web_app.py` 에 blocked-only precondition/unblock 과 capability/apply surface 분리를 잠그는 focused unittest 1건을 추가했고, `python3 -m unittest -v tests.test_smoke tests.test_web_app` 를 green 으로 rerun 했다고 적었으므로, 이번 verify round 에서는 그 claim 이 현재 코드/문서와 실제 재실행 결과에 맞는지 다시 확인했습니다. 같은 날 기존 최신 `/verify` 는 docs-sync helper family 검수 메모였기 때문에 먼저 읽고 이어받았고, 이번에는 reviewed-memory family 안에서 다음 exact slice 를 다시 좁혔습니다.

## 핵심 변경

- `ls -lt work/4/15` 기준 최신 `/work` 는 `work/4/15/2026-04-15-reviewed-memory-precondition-status-blocked-only-parity-bundle.md` 였고, `ls -lt verify/4/15` 기준 기존 최신 `/verify` 는 `verify/4/15/2026-04-15-browser-smoke-root-doc-markdown-container-helper-direct-coverage-bundle-verification.md` 였습니다. 이번 round 는 그 뒤를 잇는 reviewed-memory truth check 입니다.
- `git diff --unified=8 -- tests/test_web_app.py` 와 `sed -n '3270,3475p' tests/test_web_app.py` 확인 결과, `/work` 가 말한 `test_recurrence_aggregate_precondition_blocked_stays_fixed_when_capability_unblocked` 메서드가 실제로 additive 하게 들어가 있습니다. 같은 파일에는 dirty worktree 때문에 unrelated pending hunks 도 공존하지만, `/work` 는 dirty 상태를 이미 명시하고 있어 이번 parity 메서드 claim 자체는 현재 truth 와 맞습니다.
- `app/serializers.py` 는 여전히 `reviewed_memory_precondition_status.overall_status = blocked_all_required`, `reviewed_memory_unblock_contract.unblock_status = blocked_all_required` 를 고정하고, `reviewed_memory_capability_status.capability_outcome` 만 capability basis 유무에 따라 `unblocked_all_required` / `blocked_all_required` 로 갈라집니다. `app/handlers/aggregate.py` 도 emit/apply gating 을 `reviewed_memory_capability_status.capability_outcome` 에 묶고 있어 `/work` 설명과 일치합니다.
- Codex 가 isolated 신규 테스트를 먼저 rerun 했고 `ok` 였습니다. 이어 `/work` 가 기록한 `python3 -m unittest -v tests.test_smoke tests.test_web_app` 도 다시 실행한 결과 `Ran 368 tests in 113.479s`, `OK` 였습니다. 따라서 이번 `/work` 의 검증 claim 도 현재 truth 와 맞습니다.
- 다음 exact slice 는 `reviewed-memory boundary-draft draft-only apply-separation parity bundle` 로 좁혔습니다. `docs/NEXT_STEPS.md`, `docs/MILESTONES.md`, `docs/TASK_BACKLOG.md` 는 여전히 boundary draft 가 apply result 와 분리된 draft surface 로 남아야 한다고 적고 있고, 현재 `tests/test_web_app.py` 검색 결과 `boundary_stage = draft_not_applied` 는 initial aggregate shape assert 에만 직접 잠겨 있어 emitted/apply/stopped/reversed/conflict lifecycle 전반에서 boundary draft parity 를 직접 이름 붙인 focused regression 은 아직 없습니다.

## 검증

- `python3 -m unittest -v tests.test_web_app.WebAppServiceTest.test_recurrence_aggregate_precondition_blocked_stays_fixed_when_capability_unblocked`
  - 결과: `Ran 1 test in 3.855s`, `OK`
- `python3 -m unittest -v tests.test_smoke tests.test_web_app`
  - 결과: `Ran 368 tests in 113.479s`, `OK`
- `git diff --check -- tests/test_web_app.py app/serializers.py app/handlers/aggregate.py docs/NEXT_STEPS.md`
  - 결과: whitespace 경고 없음
- `git diff --unified=8 -- tests/test_web_app.py`
  - 결과: 신규 parity 테스트 hunk 확인, 동일 파일 내 다른 pending hunk 공존 확인
- `rg -n "reviewed_memory_boundary_draft|boundary_stage|draft_not_applied|future_reviewed_memory_stop_apply|future_reviewed_memory_reversal|future_reviewed_memory_conflict_visibility" tests/test_web_app.py`
  - 결과: `boundary_stage = draft_not_applied` 직접 assert 는 initial aggregate-shape 지점들에 한정되고, lifecycle parity 전용 regression 은 아직 없음
- `sed -n '90,170p' docs/NEXT_STEPS.md`
- `sed -n '430,490p' docs/MILESTONES.md`
- `sed -n '140,220p' docs/TASK_BACKLOG.md`
  - 결과: next priority text 는 reviewed-memory boundary draft 를 draft-only surface 로 유지하는 same-family risk reduction 을 계속 가리킴
- Playwright / `make e2e-test` 는 rerun 하지 않았습니다. 이번 verify round 는 service/unit contract 와 `/work` claim 재확인에 한정됐고 browser DOM/UI 파일은 바뀌지 않았기 때문입니다.

## 남은 리스크

- `tests/test_web_app.py` 는 이번 parity 메서드 외에도 unrelated pending hunks 를 포함한 dirty 파일입니다. 이번 verify round 는 그것들을 되돌리지 않았고, `/work` 가 설명한 parity slice 가 실제로 존재하는지만 대조했습니다.
- 현재 suite 는 blocked-only precondition/unblock 분리를 잠그지만, `reviewed_memory_boundary_draft` 가 emitted/apply/result/stopped/reversed/conflict lifecycle 전반에서도 계속 `draft_not_applied` 인 basis ref 로 남는지 직접 잠그는 focused regression 은 아직 없습니다. 이 점을 다음 handoff 로 넘깁니다.
- shared browser/UI contract 를 건드리지 않았으므로 Playwright 는 생략했지만, 다음 slice 가 aggregate 카드 노출이나 버튼 상태를 실제로 바꾸면 isolated browser rerun 또는 broader browser smoke 가 필요할 수 있습니다.
