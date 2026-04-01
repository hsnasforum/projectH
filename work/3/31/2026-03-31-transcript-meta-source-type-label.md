# 2026-03-31 transcript message meta에 summary source-type label 추가 

## 변경 파일
- `app/templates/index.html`
- `README.md`
- `docs/PRODUCT_SPEC.md`
- `docs/ACCEPTANCE_CRITERIA.md`

## 사용 skill
- 없음

## 변경 이유
- quick-meta에는 `문서 요약` / `선택 결과 요약` 구분이 이미 보이지만, 세션 히스토리 transcript의 각 메시지 meta에서는 같은 구분이 없어서, 과거 메시지를 다시 볼 때 어떤 종류의 요약이었는지 알 수 없었음

## 핵심 변경

### UI 변경
- `renderTranscript` 내 assistant message의 `metaLines`에 summary source-type label 추가:
  - `message.active_context.kind === "search"` → `선택 결과 요약`
  - `message.active_context.kind === "document"` + `summary_chunks` 또는 `evidence` 존재 → `문서 요약`
  - 일반 채팅/기타 → label 미표시
- quick-meta의 `renderResponseSummary`와 동일한 boundary 재사용
- 기존 `active_context.kind` 값을 재활용하여 새 backend field 불필요

### 변경하지 않은 것
- `app/web.py`: 변경 없음
- `core/agent_loop.py`: 변경 없음
- summary prompt / behavior: 변경 없음
- quick-meta: 기존 동작 유지

### docs 반영 (3개 파일)
- `README.md`: quick-meta → "both quick-meta bar and transcript message meta" 표현 수정
- `docs/PRODUCT_SPEC.md`: 동일
- `docs/ACCEPTANCE_CRITERIA.md`: 동일

## 검증
- `git diff --check` — 통과
- `make e2e-test` — `12 passed (2.7m)`

## 남은 리스크
- mock adapter 환경에서는 search mode가 실행되지 않으므로 `선택 결과 요약` transcript label을 dedicated assertion으로 고정할 수 없음
- `문서 요약` transcript label은 시나리오 1에서 간접적으로 확인 가능 (response에 evidence + summary_chunks가 있고 active_context.kind가 document)
- dirty worktree는 여전히 넓음 (이번 라운드에서 unrelated 변경을 건드리지 않음)
