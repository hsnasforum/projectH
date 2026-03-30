# 2026-03-27 First memory trace implementation cut

## 변경 파일

- `docs/NEXT_STEPS.md`
- `docs/MILESTONES.md`
- `docs/TASK_BACKLOG.md`
- `docs/PRODUCT_SPEC.md`
- `docs/ARCHITECTURE.md`
- `docs/ACCEPTANCE_CRITERIA.md`
- `plandoc/2026-03-27-first-memory-trace-implementation-cut.md`

## 사용 skill

- `mvp-scope`: 이미 고정된 memory 정책을 다시 열지 않고, 이번 라운드 범위를 `first implementation slice` 선택과 roadmap 재정렬로만 좁히기 위해 사용
- `doc-sync`: 현재 raw trace 구현 현실과 `NEXT_STEPS` / spec / architecture / acceptance / milestone / backlog 문서를 맞추기 위해 사용
- `release-check`: first slice, later stage, eval-ready, review queue 용어가 섞이지 않는지 점검하고 미실행 검증을 분리해 적기 위해 사용
- `work-log-closeout`: 2026-03-27 라운드의 변경 파일, 검증, 이어받은 리스크, 남은 리스크를 저장소 규칙에 맞춰 남기기 위해 사용

## 변경 이유

- 이전 closeout에서 이어받은 리스크:
  - category별 recurrence tuning은 아직 미정이었습니다.
  - approval-backed save 가중치의 category별 세부 튜닝은 아직 미정이었습니다.
  - 일부 repository-shaped workflow에서 `path_family` 예외가 필요한지 아직 미정이었습니다.
  - review / rollback UI 이후 어떤 fixture family를 e2e로 올릴지 아직 미정이었습니다.
  - 첫 operator surface는 여전히 future stage에 남겨야 했습니다.
- 이번 라운드는 위 policy를 다시 열지 않고, “실제 구현을 시작한다면 무엇을 먼저 만들 것인가”를 하나로 고정하는 작업이었습니다.
- 특히 `docs/NEXT_STEPS.md`가 최신 roadmap과 어긋나 있었기 때문에, 다음 단계 진입점과 예상 파일/테스트 방향을 현재 문서 세트에 맞게 동기화해야 했습니다.

## 핵심 변경

- first implementation slice를 `artifact_id` 생성과 `message / approval / task-log` linkage로 고정했습니다.
- `docs/NEXT_STEPS.md`를 현재 checkpoint, first slice 정의, 예상 변경 파일, later-stage 분리 구조로 다시 정렬했습니다.
- `docs/PRODUCT_SPEC.md`, `docs/ARCHITECTURE.md`, `docs/ACCEPTANCE_CRITERIA.md`에 first slice의 목표, 비목표, additive field, 검증 방향을 반영했습니다.
- `docs/MILESTONES.md`와 `docs/TASK_BACKLOG.md`의 우선순위를 review queue나 user-level memory보다 trace anchor implementation-first 순서로 갱신했습니다.
- 새 문서 `plandoc/2026-03-27-first-memory-trace-implementation-cut.md`를 추가해 왜 `artifact_id` linkage가 가장 작은 가치 있는 시작점인지, 어떤 파일과 테스트가 먼저 움직일지, 무엇을 아직 구현하지 않을지를 한 곳에 고정했습니다.
- 이번 라운드에서 해소한 리스크:
  - first implementation slice 미정 상태
  - `docs/NEXT_STEPS.md`의 roadmap drift
  - 첫 테스트 시작점과 rollback-friendly 구현 순서 부재

## 검증

- 확인: `sed -n '1,220p' work/3/27/2026-03-27-grounded-brief-eval-fixture-matrix.md`
- 확인: `sed -n '1,260p' plandoc/2026-03-26-teachable-local-agent-roadmap.md`
- 확인: `sed -n '1,260p' plandoc/2026-03-26-grounded-brief-memory-contract.md`
- 확인: `sed -n '1,260p' plandoc/2026-03-26-durable-candidate-review-surface.md`
- 확인: `sed -n '1,260p' plandoc/2026-03-26-suggested-scope-and-save-weighting-policy.md`
- 확인: `sed -n '1,260p' plandoc/2026-03-27-grounded-brief-eval-fixture-matrix.md`
- 확인: `sed -n '1,260p' AGENTS.md`
- 확인: `sed -n '1,240p' CLAUDE.md`
- 확인: `sed -n '1,260p' PROJECT_CUSTOM_INSTRUCTIONS.md`
- 확인: `sed -n '1,220p' .agents/skills/mvp-scope/SKILL.md`
- 확인: `sed -n '1,220p' .agents/skills/doc-sync/SKILL.md`
- 확인: `sed -n '1,220p' .agents/skills/release-check/SKILL.md`
- 확인: `sed -n '1,220p' .agents/skills/work-log-closeout/SKILL.md`
- 확인: `sed -n '1,320p' docs/PRODUCT_SPEC.md`
- 확인: `sed -n '1,320p' docs/ARCHITECTURE.md`
- 확인: `sed -n '1,320p' docs/ACCEPTANCE_CRITERIA.md`
- 확인: `sed -n '1,260p' docs/MILESTONES.md`
- 확인: `sed -n '1,260p' docs/TASK_BACKLOG.md`
- 확인: `sed -n '1,260p' docs/NEXT_STEPS.md`
- 확인: `sed -n '1,220p' README.md`
- 확인: `sed -n '1,260p' core/agent_loop.py`
- 확인: `sed -n '1,260p' storage/session_store.py`
- 확인: `sed -n '1,220p' storage/task_log.py`
- 확인: `sed -n '1,260p' app/web.py`
- 확인: `sed -n '1,260p' tests/test_smoke.py`
- 확인: `sed -n '1,260p' tests/test_web_app.py`
- 실행: `rg -n "approval_requested|approval_granted|approval_rejected|approval_reissued|response_feedback_recorded|saved_note_path|note_preview|summary_chunks|evidence|message_id|feedback" core/agent_loop.py storage/session_store.py storage/task_log.py app/web.py tests/test_smoke.py tests/test_web_app.py`
- 실행: `nl -ba core/agent_loop.py | sed -n '5880,6215p'`
- 실행: `nl -ba core/agent_loop.py | sed -n '6640,7118p'`
- 실행: `nl -ba app/web.py | sed -n '720,790p'`
- 실행: `nl -ba tests/test_web_app.py | sed -n '240,320p'`
- 실행: `nl -ba tests/test_smoke.py | sed -n '2870,2960p'`
- 실행: `rg -n "first implementation slice|artifact_id|artifact_kind|raw snapshot|raw trace|eval-ready|later stage|review queue|user-level memory" docs/PRODUCT_SPEC.md docs/ARCHITECTURE.md docs/ACCEPTANCE_CRITERIA.md docs/MILESTONES.md docs/TASK_BACKLOG.md docs/NEXT_STEPS.md plandoc/2026-03-27-first-memory-trace-implementation-cut.md`
- 실행: `git diff --check -- docs/NEXT_STEPS.md docs/MILESTONES.md docs/TASK_BACKLOG.md docs/PRODUCT_SPEC.md docs/ARCHITECTURE.md docs/ACCEPTANCE_CRITERIA.md plandoc/2026-03-27-first-memory-trace-implementation-cut.md`
- 실행: `rg -n "first implementation slice|raw trace reuse|eval-ready|later stage|artifact_id linkage|trace anchor" docs/NEXT_STEPS.md docs/MILESTONES.md docs/TASK_BACKLOG.md docs/PRODUCT_SPEC.md docs/ARCHITECTURE.md docs/ACCEPTANCE_CRITERIA.md plandoc/2026-03-27-first-memory-trace-implementation-cut.md`
- 미실행: `python3 -m unittest -v`
- 미실행: `make e2e-test`

## 남은 리스크

- 여전히 남은 리스크:
  - `response_feedback_recorded`가 `artifact_id`를 직접 log detail에 남길지, message lookup으로만 복원할지 아직 미정입니다.
  - first slice에서 approval public payload까지 `artifact_id`를 노출할지, 내부/session trace에 먼저 둘지 아직 미정입니다.
  - additive optional field만으로 충분한지, later slice에서 별도 artifact store가 언제 필요한지 아직 미정입니다.
  - category별 recurrence tuning은 계속 미정이며 이번 라운드에서 열지 않았습니다.
  - approval-backed save 가중치의 category별 세부 튜닝은 계속 미정이며 이번 라운드에서 열지 않았습니다.
  - 일부 repository-shaped workflow에서 `path_family` 예외가 필요한지 계속 미정입니다.
  - review / rollback UI 이후 어떤 fixture family를 e2e로 올릴지 계속 미정입니다.
  - 첫 operator surface는 계속 future stage에 남겨 두었습니다.
