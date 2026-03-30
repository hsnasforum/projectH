# 2026-03-26 Memory promotion policy doc sync

## 변경 파일

- `docs/PRODUCT_SPEC.md`
- `docs/ARCHITECTURE.md`
- `docs/ACCEPTANCE_CRITERIA.md`
- `docs/MILESTONES.md`
- `docs/TASK_BACKLOG.md`
- `plandoc/2026-03-26-grounded-brief-memory-contract.md`

## 사용 skill

- `mvp-scope`: 이전 closeout의 단계 구분과 `grounded brief` 고정을 유지한 채 이번 라운드 범위를 `승격 정책`, `reason taxonomy`, `session/user memory 경계`로 좁히기 위해 사용
- `doc-sync`: spec, architecture, acceptance, milestones, backlog, plandoc을 실제 구현의 feedback / approval / trace 구조와 맞춰 정렬하기 위해 사용
- `release-check`: 용어 일관성, 현재 계약과 다음 단계 설계 구분, 미실행 검증 표기를 점검하기 위해 사용
- `work-log-closeout`: 이번 라운드의 변경 이유, 검증, 남은 리스크를 저장소 규칙에 맞춰 남기기 위해 사용

## 변경 이유

- 이전 closeout에서 이어받은 리스크:
  - durable preference memory 승격 규칙이 아직 `OPEN QUESTION`
  - approval reject / reissue reason taxonomy와 correction reason taxonomy 관계가 아직 `OPEN QUESTION`
  - user-level memory 와 session-level memory 경계가 아직 `OPEN QUESTION`
  - 첫 operator surface는 계속 미정이며 future stage에 머물러야 함
- 이번 라운드는 위 리스크 중 앞의 세 가지를 가장 작은 문서 계약으로 더 구체화하는 단계였습니다.
- 현재 shipped contract는 계속 `로컬 퍼스트 문서 비서 웹 MVP`로 유지하고, 프로그램 조작과 모델 학습은 계속 future stage로 남겨야 했습니다.

## 핵심 변경

- `docs/PRODUCT_SPEC.md`와 `plandoc/2026-03-26-grounded-brief-memory-contract.md`에 `session_local -> durable_candidate` 최소 승격 정책을 고정했습니다.
  - `session_local`은 one-off / ambiguous / trace-incomplete signal의 기본 상태로 둡니다.
  - `durable_candidate`는 trace-complete candidate record가 있고, `grounded brief` 2회 반복 또는 명시적 사용자 확인이 있을 때만 허용합니다.
  - approval trace는 있으면 연결해야 하지만, 현재 save flow에만 존재하므로 유일한 최소 gate로 두지 않았습니다.
- `docs/PRODUCT_SPEC.md`, `docs/ARCHITECTURE.md`, `docs/ACCEPTANCE_CRITERIA.md`, `plandoc/2026-03-26-grounded-brief-memory-contract.md`에 `shared fields + distinct label sets` 구조를 고정했습니다.
  - shared fields: `reason_scope`, `reason_label`, `reason_note`
  - correction label은 현재 feedback reason에 최대한 가깝게 유지
  - approval reject / reissue는 전용 label set으로 분리
- `docs/PRODUCT_SPEC.md`, `docs/ARCHITECTURE.md`, `docs/ACCEPTANCE_CRITERIA.md`에 session-level memory와 future user-level memory 경계를 명시했습니다.
  - `session_local`은 현재 세션과 immediate follow-up에 붙는 개념
  - `durable_candidate`는 세션 밖으로 남을 수 있지만 reviewable local candidate일 뿐 user-level memory는 아님
  - user-level memory는 review / rollback / scope / conflict surface가 생긴 뒤의 future target으로 제한
- `docs/ACCEPTANCE_CRITERIA.md`, `docs/MILESTONES.md`, `docs/TASK_BACKLOG.md`에 acceptance / eval / next-priority 문구를 갱신했습니다.
  - correction reason 감소와 approval friction 감소를 분리해서 보도록 정리
  - artifact -> evidence -> reason -> approval -> outcome trace 완전성을 다음 단계 eval placeholder로 고정
- 이번 라운드에서 해소한 리스크:
  - 최소 승격 정책 부재
  - reason taxonomy 관계 부재
  - session-level vs user-level memory 경계 부재

## 검증

- 확인: `sed -n '1,220p' work/3/26/2026-03-26-brief-memory-contract-doc-sync.md`
- 확인: `sed -n '1,260p' plandoc/2026-03-26-teachable-local-agent-roadmap.md`
- 확인: `sed -n '1,260p' plandoc/2026-03-26-grounded-brief-memory-contract.md`
- 확인: `sed -n '1,260p' AGENTS.md`
- 확인: `sed -n '1,220p' CLAUDE.md`
- 확인: `sed -n '1,240p' PROJECT_CUSTOM_INSTRUCTIONS.md`
- 확인: `sed -n '1,220p' README.md`
- 확인: `sed -n '1,430p' docs/PRODUCT_SPEC.md`
- 확인: `sed -n '1,316p' docs/ARCHITECTURE.md`
- 확인: `sed -n '1,140p' docs/ACCEPTANCE_CRITERIA.md`
- 확인: `sed -n '1,116p' docs/MILESTONES.md`
- 확인: `sed -n '1,109p' docs/TASK_BACKLOG.md`
- 확인: `sed -n '1,260p' storage/session_store.py`
- 확인: `sed -n '1,220p' storage/task_log.py`
- 확인: `sed -n '90,170p' app/web.py`
- 확인: `sed -n '250,360p' app/web.py`
- 확인: `sed -n '720,1010p' app/web.py`
- 확인: `sed -n '1,180p' core/agent_loop.py`
- 확인: `sed -n '1010,1105p' core/agent_loop.py`
- 확인: `sed -n '5970,6215p' core/agent_loop.py`
- 확인: `sed -n '6640,6905p' core/agent_loop.py`
- 확인: `sed -n '7000,7085p' core/agent_loop.py`
- 실행: `rg -n "grounded brief|artifact_id|session_local|durable_candidate|reason_label|reason_note|feedback|approval|reissue|reject|user-level|memory|preference|evidence" README.md docs/PRODUCT_SPEC.md docs/ARCHITECTURE.md docs/ACCEPTANCE_CRITERIA.md docs/MILESTONES.md docs/TASK_BACKLOG.md core/agent_loop.py storage/session_store.py storage/task_log.py app/web.py`
- 실행: `rg -n "session_local|durable_candidate|user-level memory|reason_scope|reason_label|approval_reject|approval_reissue|path_change|filename_preference|directory_preference" docs/PRODUCT_SPEC.md docs/ARCHITECTURE.md docs/ACCEPTANCE_CRITERIA.md docs/MILESTONES.md docs/TASK_BACKLOG.md plandoc/2026-03-26-grounded-brief-memory-contract.md`
- 실행: `git diff --check -- docs/PRODUCT_SPEC.md docs/ARCHITECTURE.md docs/ACCEPTANCE_CRITERIA.md docs/MILESTONES.md docs/TASK_BACKLOG.md plandoc/2026-03-26-grounded-brief-memory-contract.md work/3/26/2026-03-26-memory-promotion-policy-doc-sync.md`
- 미실행: `python3 -m unittest -v`
- 미실행: `make e2e-test`

## 남은 리스크

- 여전히 남은 리스크:
  - 기본 recurrence rule을 모든 candidate category에 대해 `grounded brief` 2회로 둘지, category별로 조정할지 아직 미정입니다.
  - 명시적 사용자 확인이 없을 때 approval-backed save에 얼마나 가중치를 줄지 아직 미정입니다.
  - `durable_candidate`를 future user-level memory로 올리기 위한 review / scope / rollback surface는 아직 future design target입니다.
  - 첫 operator surface는 계속 미정이며, 이번 라운드에서도 future stage를 넘겨 확정하지 않았습니다.
