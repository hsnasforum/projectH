# 2026-03-26 Durable candidate review surface doc sync

## 변경 파일

- `docs/PRODUCT_SPEC.md`
- `docs/ARCHITECTURE.md`
- `docs/ACCEPTANCE_CRITERIA.md`
- `docs/MILESTONES.md`
- `docs/TASK_BACKLOG.md`
- `plandoc/2026-03-26-grounded-brief-memory-contract.md`
- `plandoc/2026-03-26-durable-candidate-review-surface.md`

## 사용 skill

- `mvp-scope`: 이전 closeout의 단계 구분을 유지한 채 이번 라운드 범위를 `review surface`, `scope/conflict/rollback`, `acceptance placeholder`로만 좁히기 위해 사용
- `doc-sync`: spec, architecture, acceptance, milestones, backlog, plandoc을 실제 구현의 feedback / approval / trace 구조와 맞춰 정렬하기 위해 사용
- `release-check`: 용어 일관성, current / future 구분, 미실행 검증 표기를 점검하기 위해 사용
- `work-log-closeout`: 이번 라운드의 변경 파일, 검증, 남은 리스크를 저장소 규칙에 맞춰 남기기 위해 사용

## 변경 이유

- 이전 closeout에서 이어받은 리스크:
  - `durable_candidate`를 future user-level memory로 올리기 전에 필요한 review / scope / rollback surface가 아직 미정이었습니다.
  - category별 recurrence tuning과 approval-backed save 가중치는 아직 미정이었고, 이번 라운드에서도 함부로 확정하면 안 됐습니다.
  - 첫 operator surface는 계속 미정이며 future stage에 남겨야 했습니다.
- 이번 라운드는 위 리스크 중 첫 번째를 가장 작은 문서 계약으로 고정하고, 나머지 둘은 계속 `OPEN QUESTION`으로 남기는 작업이었습니다.
- 현재 shipped contract는 계속 `로컬 퍼스트 문서 비서 웹 MVP`로 유지하고, user-level memory / 프로그램 조작 / 모델 학습을 현재 기능처럼 쓰지 않아야 했습니다.

## 핵심 변경

- `docs/PRODUCT_SPEC.md`에 future user-level memory 이전 단계로서 `review queue`, `accept / edit / reject / defer`, `scope / conflict / rollback` 원칙을 추가했습니다.
- `docs/ARCHITECTURE.md`에 future review queue가 current session JSON과 다른 별도 local surface여야 하고, review / rollback trace가 append-only audit처럼 남아야 한다는 원칙을 정리했습니다.
- `docs/ACCEPTANCE_CRITERIA.md`에 reviewed vs unreviewed 구분, rollback 후 미적용, conflict trace 유지, current gate와 future placeholder 분리를 추가했습니다.
- `docs/MILESTONES.md`와 `docs/TASK_BACKLOG.md`에서 다음 단계 우선순위를 `reviewable durable candidate surface` 쪽으로 한 단계 전진시켰습니다.
- 새 문서 `plandoc/2026-03-26-durable-candidate-review-surface.md`를 추가해 review queue entry rule, review item 필드, scope 후보, conflict 원칙, rollback 원칙, acceptance/eval placeholder를 분리 문서로 고정했습니다.
- 이번 라운드에서 해소한 리스크:
  - 최소 review surface 부재
  - 최소 scope / conflict / rollback 원칙 부재
  - reviewed vs unreviewed / rollback / conflict placeholder 부재

## 검증

- 확인: `sed -n '1,240p' work/3/26/2026-03-26-memory-promotion-policy-doc-sync.md`
- 확인: `sed -n '1,260p' plandoc/2026-03-26-teachable-local-agent-roadmap.md`
- 확인: `sed -n '1,280p' plandoc/2026-03-26-grounded-brief-memory-contract.md`
- 확인: `sed -n '1,260p' AGENTS.md`
- 확인: `sed -n '1,240p' CLAUDE.md`
- 확인: `sed -n '1,260p' PROJECT_CUSTOM_INSTRUCTIONS.md`
- 확인: `sed -n '1,520p' docs/PRODUCT_SPEC.md`
- 확인: `sed -n '1,380p' docs/ARCHITECTURE.md`
- 확인: `sed -n '1,220p' docs/ACCEPTANCE_CRITERIA.md`
- 확인: `sed -n '1,220p' docs/MILESTONES.md`
- 확인: `sed -n '1,220p' docs/TASK_BACKLOG.md`
- 확인: `sed -n '1,220p' README.md`
- 확인: `sed -n '1,260p' storage/session_store.py`
- 확인: `sed -n '1,220p' storage/task_log.py`
- 확인: `sed -n '90,170p' app/web.py`
- 확인: `sed -n '250,360p' app/web.py`
- 확인: `sed -n '720,1010p' app/web.py`
- 확인: `sed -n '1,180p' core/agent_loop.py`
- 확인: `sed -n '5970,6215p' core/agent_loop.py`
- 확인: `sed -n '6640,7085p' core/agent_loop.py`
- 실행: `rg -n "feedback|reason|approval_requested|approval_rejected|approval_reissued|approval_granted|update_message|pending_approvals|saved_note_path|note_preview" core/agent_loop.py storage/session_store.py storage/task_log.py app/web.py`
- 실행: `rg -n "review queue|durable_candidate|future user-level memory|rollback|scope|conflict|review_status|accept|edit|reject|defer" docs/PRODUCT_SPEC.md docs/ARCHITECTURE.md docs/ACCEPTANCE_CRITERIA.md docs/MILESTONES.md docs/TASK_BACKLOG.md plandoc/2026-03-26-grounded-brief-memory-contract.md plandoc/2026-03-26-durable-candidate-review-surface.md`
- 실행: `git diff --check -- docs/PRODUCT_SPEC.md docs/ARCHITECTURE.md docs/ACCEPTANCE_CRITERIA.md docs/MILESTONES.md docs/TASK_BACKLOG.md plandoc/2026-03-26-grounded-brief-memory-contract.md plandoc/2026-03-26-durable-candidate-review-surface.md work/3/26/2026-03-26-durable-candidate-review-surface-doc-sync.md`
- 미실행: `python3 -m unittest -v`
- 미실행: `make e2e-test`

## 남은 리스크

- 여전히 남은 리스크:
  - category별 recurrence tuning은 아직 미정입니다.
  - 명시적 사용자 확인이 없을 때 approval-backed save에 얼마만큼 가중치를 줄지는 아직 미정입니다.
  - `global`, `document_type`, `path_family`, `workflow_type`가 모두 맞을 때 기본 suggested scope를 무엇으로 둘지 아직 미정입니다.
  - 첫 operator surface는 계속 미정이며, 이번 라운드에서도 future stage를 넘겨 확정하지 않았습니다.
