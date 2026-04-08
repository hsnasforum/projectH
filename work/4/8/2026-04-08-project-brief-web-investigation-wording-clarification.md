# project-brief Web Investigation wording clarification

## 변경 파일

- `docs/project-brief.md`

## 사용 skill

- 없음 (문서 전용 슬라이스)

## 변경 이유

`docs/project-brief.md`의 Current Contract, Implemented 목록, Data Assets trace 문구가 출하된 웹 조사 기능의 세부 사항을 충분히 반영하지 못하고 있었음. `docs/TASK_BACKLOG.md`, `README.md`, `docs/PRODUCT_SPEC.md`, `docs/ACCEPTANCE_CRITERIA.md`는 이미 정밀하게 정렬되어 있으므로 root-level brief만 동일한 수준으로 맞춤.

## 핵심 변경

1. **Current Contract (line 15)**: `permission-gated web investigation with local history` → `(enabled/disabled/ask per session) with local JSON history, in-session reload, and history-card badges` 명시
2. **Current Contract (line 16)**: `secondary mode` 뒤에 `under the document-first guardrail` 추가
3. **Implemented (lines 79-81)**: 기존 2줄을 3줄로 분리
   - web investigation에 permission states, history-card badge 종류 (answer-mode, verification-strength, source-role trust) 명시
   - entity-card / latest-update answer-mode distinction 및 entity-card strong-badge downgrade 별도 줄 추가
   - claim coverage panel with status tags and actionable hints 별도 줄 추가
4. **Data Assets trace (line 107)**: `web investigation traces` → `web investigation local JSON history and history-card badge traces` 구체화

## 검증

- `git diff -- docs/project-brief.md`: 5줄 삭제, 6줄 추가 확인
- `git diff --check -- docs/project-brief.md`: whitespace 에러 없음
- `nl -ba docs/project-brief.md | sed -n '13,18p;68,83p;100,109p'`: 핵심 라인 정렬 확인 완료

## 남은 리스크

- `docs/PRODUCT_PROPOSAL.md`도 유사하게 일반적이지만, 핸드오프 범위에서 명시적으로 제외됨. 별도 슬라이스 필요.
- `docs/project-brief.md`의 나머지 섹션(OPEN QUESTION, Next 3 Priorities 등)은 이번 슬라이스 범위 밖.
