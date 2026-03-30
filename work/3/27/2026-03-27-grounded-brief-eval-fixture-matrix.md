# 2026-03-27 Grounded brief eval fixture matrix

## 변경 파일

- `docs/PRODUCT_SPEC.md`
- `docs/ARCHITECTURE.md`
- `docs/ACCEPTANCE_CRITERIA.md`
- `docs/MILESTONES.md`
- `docs/TASK_BACKLOG.md`
- `plandoc/2026-03-27-grounded-brief-eval-fixture-matrix.md`

## 사용 skill

- `mvp-scope`: 기존 policy를 다시 열지 않고 이번 라운드 범위를 `workflow-grade eval fixture matrix`, `eval-ready trace contract`, `eval axis separation`으로만 좁히기 위해 사용
- `doc-sync`: acceptance, milestones, backlog, spec, architecture, plandoc을 현재 message / approval / feedback / task-log trace 현실과 맞춰 정렬하기 위해 사용
- `release-check`: 용어 일관성, current gate / future placeholder / future implementation target 구분, 미실행 검증 표기를 점검하기 위해 사용
- `work-log-closeout`: 2026-03-27 라운드의 변경 파일, 검증, 남은 리스크를 저장소 규칙에 맞춰 남기기 위해 사용

## 변경 이유

- 이전 closeout에서 이어받은 리스크:
  - category별 recurrence tuning은 여전히 미정이었습니다.
  - approval-backed save 가중치의 category별 세부 튜닝은 여전히 미정이었습니다.
  - 일부 repository-shaped workflow에서 `path_family`를 `workflow_type`보다 먼저 제안해야 할 예외는 여전히 미정이었습니다.
  - 첫 operator surface는 계속 future stage에 남겨야 했습니다.
- 이번 라운드는 위 미결 리스크를 다시 열지 않고, 이미 고정된 memory / review / scope / save-weighting 정책을 실제로 평가 가능한 fixture family와 trace contract 수준으로 정리하는 작업이었습니다.
- current shipped contract는 계속 `로컬 퍼스트 문서 비서 웹 MVP`로 유지하고, workflow-grade eval을 current gate가 아니라 future placeholder / implementation target으로 분리해야 했습니다.

## 핵심 변경

- `docs/ACCEPTANCE_CRITERIA.md`에 `eval-ready artifact` core chain, family-specific trace extension rule, eval axis separation, 그리고 7개 `GB-EVAL-*` fixture family placeholder를 추가했습니다.
- `docs/MILESTONES.md`와 `docs/TASK_BACKLOG.md`에서 다음 우선순위를 fixture matrix, trace contract, eval axis separation 쪽으로 갱신했습니다.
- `docs/PRODUCT_SPEC.md`와 `docs/ARCHITECTURE.md`에 workflow-grade eval baseline과 eval-ready artifact trace contract 요약을 추가했습니다.
- 새 문서 `plandoc/2026-03-27-grounded-brief-eval-fixture-matrix.md`를 추가해 fixture family별 scenario, 입력 조건, 필요한 trace, 기대 결과, 미구현 요소, future test level을 한 곳에 고정했습니다.
- 이번 라운드에서 해소한 리스크:
  - workflow-grade eval fixture family 부재
  - eval-ready artifact trace contract 부재
  - correction reuse / approval friction / scope safety / reviewability / trace completeness 축 분리 부재

## 검증

- 확인: `sed -n '1,220p' work/3/26/2026-03-26-suggested-scope-save-weighting-doc-sync.md`
- 확인: `sed -n '1,260p' plandoc/2026-03-26-teachable-local-agent-roadmap.md`
- 확인: `sed -n '1,280p' plandoc/2026-03-26-grounded-brief-memory-contract.md`
- 확인: `sed -n '1,260p' plandoc/2026-03-26-durable-candidate-review-surface.md`
- 확인: `sed -n '1,260p' plandoc/2026-03-26-suggested-scope-and-save-weighting-policy.md`
- 확인: `sed -n '1,260p' AGENTS.md`
- 확인: `sed -n '1,240p' CLAUDE.md`
- 확인: `sed -n '1,260p' PROJECT_CUSTOM_INSTRUCTIONS.md`
- 확인: `sed -n '1,220p' .agents/skills/mvp-scope/SKILL.md`
- 확인: `sed -n '1,220p' .agents/skills/doc-sync/SKILL.md`
- 확인: `sed -n '1,220p' .agents/skills/release-check/SKILL.md`
- 확인: `sed -n '1,220p' .agents/skills/work-log-closeout/SKILL.md`
- 확인: `sed -n '1,320p' docs/PRODUCT_SPEC.md`
- 확인: `sed -n '1,320p' docs/ARCHITECTURE.md`
- 확인: `sed -n '1,260p' docs/ACCEPTANCE_CRITERIA.md`
- 확인: `sed -n '1,240p' docs/MILESTONES.md`
- 확인: `sed -n '1,240p' docs/TASK_BACKLOG.md`
- 확인: `sed -n '1,220p' README.md`
- 확인: `sed -n '1,220p' core/agent_loop.py`
- 확인: `sed -n '1,260p' storage/session_store.py`
- 확인: `sed -n '1,220p' storage/task_log.py`
- 확인: `sed -n '1,260p' app/web.py`
- 실행: `rg -n "approval_requested|approval_granted|approval_rejected|approval_reissued|response_feedback_recorded|saved_note_path|note_preview|claim_coverage|summary_chunks|evidence|message_id" core/agent_loop.py storage/session_store.py storage/task_log.py app/web.py`
- 실행: `rg -n "eval-ready artifact|fixture family|trace completeness|approval friction|correction reuse|manual inspection placeholder|service fixture|unit helper|e2e later" docs/PRODUCT_SPEC.md docs/ARCHITECTURE.md docs/ACCEPTANCE_CRITERIA.md docs/MILESTONES.md docs/TASK_BACKLOG.md plandoc/2026-03-27-grounded-brief-eval-fixture-matrix.md`
- 실행: `git diff --check -- docs/PRODUCT_SPEC.md docs/ARCHITECTURE.md docs/ACCEPTANCE_CRITERIA.md docs/MILESTONES.md docs/TASK_BACKLOG.md plandoc/2026-03-27-grounded-brief-eval-fixture-matrix.md work/3/27/2026-03-27-grounded-brief-eval-fixture-matrix.md`
- 실행: `rg -n "eval-ready artifact|fixture family|trace completeness|approval friction|correction reuse" docs/PRODUCT_SPEC.md docs/ARCHITECTURE.md docs/ACCEPTANCE_CRITERIA.md docs/MILESTONES.md docs/TASK_BACKLOG.md plandoc/2026-03-27-grounded-brief-eval-fixture-matrix.md work/3/27/2026-03-27-grounded-brief-eval-fixture-matrix.md`
- 미실행: `python3 -m unittest -v`
- 미실행: `make e2e-test`

## 남은 리스크

- 여전히 남은 리스크:
  - category별 recurrence tuning은 아직 미정입니다.
  - approval-backed save 가중치의 category별 세부 튜닝은 아직 미정입니다.
  - 일부 repository-shaped workflow에서 `path_family`를 `workflow_type`보다 먼저 제안해야 할 예외는 아직 미정입니다.
  - review / rollback UI가 생긴 뒤 어떤 fixture family까지 e2e로 올릴지 아직 미정입니다.
  - 첫 operator surface는 계속 미정이며, 이번 라운드에서도 future stage를 넘겨 확정하지 않았습니다.
