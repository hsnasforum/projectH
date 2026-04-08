# PRODUCT_PROPOSAL Web Investigation wording clarification

## 변경 파일

- `docs/PRODUCT_PROPOSAL.md`

## 사용 skill

- 없음 (문서 전용 슬라이스)

## 변경 이유

`docs/PRODUCT_PROPOSAL.md`의 Decision Frame facts, Implemented Product Surface, Core Product Boundaries, Data Assets 문구가 출하된 웹 조사 기능의 세부 사항을 충분히 반영하지 못하고 있었음. 같은 계열의 소스-오브-트루스 (`docs/project-brief.md`, `docs/TASK_BACKLOG.md`, `README.md`, `docs/PRODUCT_SPEC.md`, `docs/ACCEPTANCE_CRITERIA.md`)는 이미 정렬 완료되어 있으므로 마지막 남은 root-level framing 문서를 동일 수준으로 맞춤.

## 핵심 변경

1. **Decision Frame facts (line 26)**: `guarded secondary mode with quality work in progress` → permission-gated (enabled/disabled/ask per session), document-first guardrail, 출하된 surface 열거 (local JSON history, in-session reload, history-card badges, answer-mode distinction, claim-coverage panel)
2. **Implemented Product Surface (lines 59-61)**: 기존 1줄을 3줄로 분리
   - web investigation에 permission states, history-card badge 종류 명시
   - entity-card / latest-update answer-mode distinction 별도 줄
   - claim coverage panel with status tags and actionable hints 별도 줄
3. **Core Product Boundaries (line 65)**: `evidence-backed web investigation` → `permission-gated web investigation (enabled/disabled/ask per session) under document-first guardrail`
4. **Data Assets (line 137)**: `web investigation history` → `web investigation local JSON history and history-card badge traces` 구체화

## 검증

- `git diff -- docs/PRODUCT_PROPOSAL.md`: 4줄 삭제, 6줄 추가 확인
- `git diff --check -- docs/PRODUCT_PROPOSAL.md`: whitespace 에러 없음
- `nl -ba docs/PRODUCT_PROPOSAL.md | sed -n '24,27p;54,66p;130,138p'`: 핵심 라인 정렬 확인 완료

## 남은 리스크

- `docs/MILESTONES.md:7`도 유사하게 일반적이지만, 핸드오프에서 tie-break 대상 밖으로 남겨졌음. 별도 슬라이스 필요 여부는 Codex 판단.
- 이 슬라이스로 같은 계열(웹 조사 문구 정렬) root-level 문서가 모두 정렬 완료됨: `TASK_BACKLOG`, `README`, `PRODUCT_SPEC`, `ACCEPTANCE_CRITERIA`, `NEXT_STEPS`, `project-brief`, `PRODUCT_PROPOSAL`.
