# 2026-03-26 Brief memory contract doc sync

## 변경 파일

- `README.md`
- `docs/project-brief.md`
- `docs/PRODUCT_PROPOSAL.md`
- `docs/PRODUCT_SPEC.md`
- `docs/ARCHITECTURE.md`
- `docs/ACCEPTANCE_CRITERIA.md`
- `docs/MILESTONES.md`
- `docs/TASK_BACKLOG.md`
- `plandoc/2026-03-26-grounded-brief-memory-contract.md`

## 사용 skill

- `mvp-scope`: 이전 closeout의 단계 구분을 유지한 채 다음 단계 artifact와 memory 계약을 최소 범위로 고정하기 위해 사용
- `doc-sync`: `README.md`, spec, architecture, acceptance, milestone, backlog 문구를 실제 구현과 맞춰 정렬하기 위해 사용
- `release-check`: 문서 간 용어 일관성, 현재 계약/다음 단계/장기 북극성 구분, 미실행 검증 표기를 점검하기 위해 사용
- `work-log-closeout`: 이번 라운드의 변경 파일, 검증, 남은 리스크를 저장소 규칙에 맞춰 남기기 위해 사용

## 변경 이유

- 이전 closeout에서 남긴 세 가지 리스크를 그대로 이어받았습니다.
- `README.md`와 `docs/ACCEPTANCE_CRITERIA.md`는 새 단계 구분과 맞지 않는 부분이 있어 정렬이 필요했습니다.
- `교정/승인/선호 메모리`는 아직 `OPEN QUESTION`이 많았지만, 다음 단계로 넘어가기 위한 최소 계약 초안은 문서로 고정할 필요가 있었습니다.
- 프로그램 조작은 여전히 future stage로 남겨 두되, 첫 표면을 성급히 확정하지 않는 상태를 유지해야 했습니다.

## 핵심 변경

- 다음 단계의 단일 공식 artifact를 `grounded brief`로 고정하고, 왜 현재 codebase와 approval/evidence/feedback 흐름에 가장 잘 맞는지 `README.md`, `docs/project-brief.md`, `docs/PRODUCT_PROPOSAL.md`, `docs/PRODUCT_SPEC.md`에 반영했습니다.
- `docs/PRODUCT_SPEC.md`, `docs/ARCHITECTURE.md`, `plandoc/2026-03-26-grounded-brief-memory-contract.md`에 artifact identity, original response snapshot, corrected outcome, approval trail, reason fields, preference signal candidate, session-local vs durable candidate 구분을 최소 설계 계약으로 정리했습니다.
- `docs/ACCEPTANCE_CRITERIA.md`와 `docs/PRODUCT_SPEC.md`에 correction memory, repeated-mistake 감소, preference 반영 여부, artifact/evidence/approval trace 연속성에 대한 acceptance / eval placeholder를 추가했습니다.
- `docs/MILESTONES.md`와 `docs/TASK_BACKLOG.md`에서 artifact 선택을 더 이상 open question으로 두지 않고, 다음 단계 작업을 `grounded brief` 기준으로 재정렬했습니다.
- 프로그램 조작의 첫 표면은 문서 전반에서 계속 `OPEN QUESTION`으로 유지해, 이전 closeout의 경계 조건을 유지했습니다.

## 검증

- 확인: `sed -n '1,240p' work/3/26/2026-03-26-product-direction-doc-realignment.md`
- 확인: `sed -n '1,260p' plandoc/2026-03-26-teachable-local-agent-roadmap.md`
- 확인: `sed -n '1,260p' AGENTS.md`
- 확인: `sed -n '1,220p' CLAUDE.md`
- 확인: `sed -n '1,240p' PROJECT_CUSTOM_INSTRUCTIONS.md`
- 확인: `sed -n '1,260p' core/agent_loop.py`
- 확인: `sed -n '1,260p' storage/session_store.py`
- 확인: `sed -n '1,260p' storage/task_log.py`
- 확인: `sed -n '1,260p' app/web.py`
- 실행: `rg -n "_build_save_note_approval|approval_requested|approval_granted|approval_rejected|approval_reissued|set_active_context|active_context|summary_chunks|feedback_retry|response_feedback_recorded|claim_coverage_progress_summary|saved_note_path|note_preview" core/agent_loop.py storage/session_store.py storage/task_log.py app/web.py`
- 실행: `rg -n "grounded brief|artifact_id|assistant_message_id|reason_label|reason_note|candidate_id|session_local|durable_candidate|operator surface" README.md docs/project-brief.md docs/PRODUCT_PROPOSAL.md docs/PRODUCT_SPEC.md docs/ARCHITECTURE.md docs/ACCEPTANCE_CRITERIA.md docs/MILESTONES.md docs/TASK_BACKLOG.md plandoc/2026-03-26-grounded-brief-memory-contract.md`
- 실행: `git diff --check -- README.md docs/project-brief.md docs/PRODUCT_PROPOSAL.md docs/PRODUCT_SPEC.md docs/ARCHITECTURE.md docs/ACCEPTANCE_CRITERIA.md docs/MILESTONES.md docs/TASK_BACKLOG.md plandoc/2026-03-26-grounded-brief-memory-contract.md`
- 미실행: `python3 -m unittest -v`
- 미실행: `make e2e-test`

## 남은 리스크

- 이전 closeout에서 이어받은 리스크: `README.md`와 `docs/ACCEPTANCE_CRITERIA.md` 정렬 필요 가능성은 이번 라운드에서 해소했습니다.
- 이번 라운드에서 해소한 리스크: 공식 artifact 부재 상태와 memory 최소 계약 부재 상태를 `grounded brief` 계약 초안으로 문서화했습니다.
- 여전히 남은 리스크: durable preference memory 승격 규칙, approval reject 전용 reason taxonomy, user-level vs session-level memory 경계는 아직 `OPEN QUESTION`입니다.
- 여전히 남은 리스크: 프로그램 조작의 첫 표면은 계속 미정이며, 이번 라운드에서도 future stage 설계 목표 수준을 넘기지 않았습니다.
