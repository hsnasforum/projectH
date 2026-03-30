# 2026-03-26 Suggested scope / save weighting doc sync

## 변경 파일

- `docs/PRODUCT_SPEC.md`
- `docs/ARCHITECTURE.md`
- `docs/ACCEPTANCE_CRITERIA.md`
- `docs/MILESTONES.md`
- `docs/TASK_BACKLOG.md`
- `plandoc/2026-03-26-grounded-brief-memory-contract.md`
- `plandoc/2026-03-26-durable-candidate-review-surface.md`
- `plandoc/2026-03-26-suggested-scope-and-save-weighting-policy.md`

## 사용 skill

- `mvp-scope`: 이번 라운드 범위를 `suggested scope`, `approval-backed save weighting`, `acceptance placeholder`로만 좁혀 current / next / long-term 구분을 유지하기 위해 사용
- `doc-sync`: spec, architecture, acceptance, milestones, backlog, plandoc을 현재 approval / feedback / trace 구현과 맞춰 동기화하기 위해 사용
- `release-check`: 용어 일관성, 미실행 검증 표기, future placeholder 구분을 점검하기 위해 사용
- `work-log-closeout`: 이번 라운드의 변경 파일, 검증, 남은 리스크를 저장소 규칙에 맞게 기록하기 위해 사용

## 변경 이유

- 이전 closeout에서 이어받은 리스크:
  - `global`, `document_type`, `path_family`, `workflow_type`가 모두 맞을 때 기본 suggested scope가 아직 미정이었습니다.
  - 명시적 사용자 확인이 없을 때 approval-backed save에 어느 정도 가중치를 줄지 아직 미정이었습니다.
  - category별 recurrence tuning은 계속 미정으로 남겨야 했고, 첫 operator surface도 여전히 future stage에 남겨야 했습니다.
- 이번 라운드는 위 리스크 중 첫 번째와 두 번째를 가장 작은 문서 계약으로 고정하고, 나머지는 `OPEN QUESTION`으로 유지하는 작업이었습니다.
- 현재 shipped contract는 계속 `로컬 퍼스트 문서 비서 웹 MVP`로 유지하고, review queue / user-level memory / operator surface를 현재 기능처럼 보이지 않게 유지해야 했습니다.

## 핵심 변경

- `docs/PRODUCT_SPEC.md`, `docs/ARCHITECTURE.md`, `docs/ACCEPTANCE_CRITERIA.md`에 future review item의 기본 suggested scope 순서를 `workflow_type -> path_family -> document_type -> global`로 고정하고, broader suggestion에는 justification trace가 필요하다고 추가했습니다.
- 같은 문서들에 approval-backed save를 explicit confirmation 없는 경우 `content`에는 약한 보조 근거, `save-path acceptability`에는 중간 수준의 보조 근거로만 읽고, 단독 승격이나 broader scope 정당화 근거로 쓰지 않는다고 정리했습니다.
- `scope_candidates_considered`, `scope_suggestion_reason`, `supporting_approval_ids`, `has_explicit_confirmation`를 future review trace 최소 필드로 반영했습니다.
- `docs/MILESTONES.md`와 `docs/TASK_BACKLOG.md`의 다음 우선순위를 conservative scope suggestion과 approval-backed save supporting-only policy 쪽으로 갱신했습니다.
- 새 문서 `plandoc/2026-03-26-suggested-scope-and-save-weighting-policy.md`를 추가해 suggested scope 기본값, broader-scope 예외, save weighting baseline, acceptance/eval placeholder를 분리 메모로 고정했습니다.
- 이번 라운드에서 해소한 리스크:
  - 기본 suggested scope 부재
  - approval-backed save weighting baseline 부재
  - suggested scope / approval-backed save 검증 placeholder 부재

## 검증

- 확인: `sed -n '1,220p' work/3/26/2026-03-26-durable-candidate-review-surface-doc-sync.md`
- 확인: `sed -n '1,260p' plandoc/2026-03-26-teachable-local-agent-roadmap.md`
- 확인: `sed -n '1,260p' plandoc/2026-03-26-grounded-brief-memory-contract.md`
- 확인: `sed -n '1,260p' plandoc/2026-03-26-durable-candidate-review-surface.md`
- 확인: `sed -n '1,260p' AGENTS.md`
- 확인: `sed -n '1,260p' CLAUDE.md`
- 확인: `sed -n '1,260p' PROJECT_CUSTOM_INSTRUCTIONS.md`
- 확인: `sed -n '1,220p' .agents/skills/mvp-scope/SKILL.md`
- 확인: `sed -n '1,220p' .agents/skills/doc-sync/SKILL.md`
- 확인: `sed -n '1,220p' .agents/skills/release-check/SKILL.md`
- 확인: `sed -n '1,220p' .agents/skills/work-log-closeout/SKILL.md`
- 확인: `sed -n '1,260p' docs/PRODUCT_SPEC.md`
- 확인: `sed -n '1,260p' docs/ARCHITECTURE.md`
- 확인: `sed -n '1,240p' docs/ACCEPTANCE_CRITERIA.md`
- 확인: `sed -n '1,220p' docs/MILESTONES.md`
- 확인: `sed -n '1,220p' docs/TASK_BACKLOG.md`
- 확인: `sed -n '1,220p' README.md`
- 확인: `sed -n '1,220p' core/agent_loop.py`
- 확인: `sed -n '1,260p' storage/session_store.py`
- 확인: `sed -n '1,220p' storage/task_log.py`
- 확인: `sed -n '1,260p' app/web.py`
- 실행: `rg -n "approval_requested|approval_granted|approval_rejected|approval_reissued|feedback.reason|feedback_reason|pending_approvals|note_preview|saved_note_path" core/agent_loop.py storage/session_store.py storage/task_log.py app/web.py`
- 실행: `rg -n "suggested scope|reviewed scope|approval-backed save|explicit confirmation|supporting evidence|scope_candidates_considered|scope_suggestion_reason" docs/PRODUCT_SPEC.md docs/ARCHITECTURE.md docs/ACCEPTANCE_CRITERIA.md docs/MILESTONES.md docs/TASK_BACKLOG.md plandoc/2026-03-26-grounded-brief-memory-contract.md plandoc/2026-03-26-durable-candidate-review-surface.md plandoc/2026-03-26-suggested-scope-and-save-weighting-policy.md`
- 실행: `git diff --check -- docs/PRODUCT_SPEC.md docs/ARCHITECTURE.md docs/ACCEPTANCE_CRITERIA.md docs/MILESTONES.md docs/TASK_BACKLOG.md plandoc/2026-03-26-grounded-brief-memory-contract.md plandoc/2026-03-26-durable-candidate-review-surface.md plandoc/2026-03-26-suggested-scope-and-save-weighting-policy.md`
- 미실행: `python3 -m unittest -v`
- 미실행: `make e2e-test`

## 남은 리스크

- 여전히 남은 리스크:
  - category별 recurrence tuning은 아직 미정입니다.
  - approval-backed save 가중치를 category별로 더 세분화할지 아직 미정입니다.
  - 일부 repository-shaped workflow에서 `path_family`를 `workflow_type`보다 먼저 제안해야 할 예외가 필요한지 아직 미정입니다.
  - 첫 operator surface는 계속 미정이며, 이번 라운드에서도 future stage를 넘겨 확정하지 않았습니다.
