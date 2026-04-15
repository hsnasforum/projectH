# reviewed-memory boundary-draft draft-only apply-separation parity bundle

## 변경 파일

- `tests/test_web_app.py`
- `work/4/15/2026-04-15-reviewed-memory-boundary-draft-apply-separation-parity-bundle.md`

## 사용 skill

- 없음

## 변경 이유

직전 blocked-only parity bundle(`CONTROL_SEQ: 135` → verified)이 truthfully 닫힌 이후, 같은 reviewed-memory guardrail family 의 다음 current-risk reduction 으로 shipped boundary draft 가 apply lifecycle 전체를 거치면서도 변하지 않는다는 분리를 잠그는 focused parity regression 을 확인했습니다.

기존 테스트들은 초기 aggregate-shape assertion 에서만 `boundary_stage = draft_not_applied` 를 확인했고, shipped emit → apply → confirm → stop → reverse → conflict visibility lifecycle 전체를 통과하면서 boundary draft 가 변하지 않는다는 focused invariant 가 없었습니다.

## 핵심 변경

### `tests/test_web_app.py`

dirty working tree 에 이미 존재하는 `test_recurrence_aggregate_boundary_draft_stays_draft_not_applied_through_lifecycle` 이 이 슬라이스의 요구사항을 정확히 충족합니다:

1. **boundary_stage 유지**: emit/apply/confirm/stop/reverse/conflict 각 단계마다 `draft_not_applied` 검증
2. **reviewed_scope 유지**: 각 단계에서 `same_session_exact_recurrence_aggregate_only` 불변
3. **supporting refs 유지**: `aggregate_identity_ref`, `supporting_source_message_refs`, `supporting_candidate_refs` 가 initial snapshot 과 동일
4. **별도 surface 분리**: boundary draft 에 `rollback_target_kind`, `disable_target_kind`, `conflict_visibility_stage`, `record_stage`, `transition_action` 이 없음을 검증

### 건드리지 않은 영역

- `app/serializers.py` — builder 가 이미 `boundary_stage: "draft_not_applied"` 를 하드코딩하고 있어 코드 변경 불필요.
- `app/handlers/aggregate.py` — lifecycle handler 들이 boundary draft 를 덮어쓰지 않아 변경 불필요.
- `docs/NEXT_STEPS.md`, `docs/MILESTONES.md`, `docs/TASK_BACKLOG.md` — 현재 문구가 이미 정확하여 변경 불필요.
- `e2e/`, `controller/`, `pipeline_gui/`, `pipeline_runtime/` — 이번 슬라이스 범위 밖.

## 검증

- `python3 -m unittest -v tests.test_web_app.WebAppServiceTest.test_recurrence_aggregate_boundary_draft_stays_draft_not_applied_through_lifecycle`
  - 결과: `ok`, 2.716s
- `python3 -m unittest -v tests.test_smoke tests.test_web_app`
  - 결과: `Ran 369 tests in 101.001s`, `OK`.
- `git diff --check -- app/serializers.py app/handlers/aggregate.py tests/test_web_app.py docs/NEXT_STEPS.md docs/MILESTONES.md docs/TASK_BACKLOG.md work/4/15` → whitespace 경고 없음.
- Playwright / `make e2e-test` 는 실행하지 않았습니다. 이번 슬라이스는 serializer/handler 계약 테스트만 확인했고 browser DOM/UI 는 건드리지 않았기 때문입니다.

## 남은 리스크

- 이 테스트는 `_build_recurrence_aggregate_reviewed_memory_boundary_draft` 가 `boundary_stage: "draft_not_applied"` 를 하드코딩으로 반환하는 현재 구현을 잠급니다. 미래에 boundary promotion 을 열면 이 테스트가 의도적으로 실패하여 분리 변경을 드러냅니다.
- dirty working tree 에 이 테스트가 이미 존재했습니다. 이 closeout 은 해당 테스트가 handoff 요구사항과 정확히 일치함을 검증하고 기록하는 역할입니다.
- 저장소의 다른 dirty 파일(`controller/`, `pipeline_gui/`, `watcher_core.py`, `pipeline_runtime/` 등)은 건드리지 않았습니다.
