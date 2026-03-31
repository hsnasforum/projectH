# 2026-03-31 summary source-type label in quick-meta 

## 변경 파일
- `app/templates/index.html`
- `README.md`
- `docs/PRODUCT_SPEC.md`
- `docs/ACCEPTANCE_CRITERIA.md`

## 사용 skill
- 없음

## 변경 이유
- local document summary와 selected search-result summary의 source-type boundary가 내부적으로 존재하지만 사용자에게는 보이지 않아, "지금 답이 원문 문서 요약인지 선택 검색 결과 종합인지" 구분할 수 없었음

## 핵심 변경

### UI 변경
- `renderResponseSummary`의 quick-meta에 summary source-type label 추가:
  - `active_context.kind === "search"` → `선택 결과 요약`
  - `active_context.kind === "document"` + evidence 또는 summary_chunks 존재 → `문서 요약`
  - 일반 채팅/기타 → label 미표시
- 기존 `active_context.kind` 값을 재활용하여 새 backend field 불필요

### 변경하지 않은 것
- `core/agent_loop.py`: `AgentResponse` 필드 추가 시도 후 되돌림 — `active_context.kind`로 충분
- `app/web.py`: serialize 변경 시도 후 되돌림
- summary prompt / behavior: 변경 없음
- transcript meta: 변경 없음 (quick-meta만)

### docs 반영 (3개 파일)
- `README.md`: "summary source-type label (`문서 요약` / `선택 결과 요약`)" 추가
- `docs/PRODUCT_SPEC.md`: 동일
- `docs/ACCEPTANCE_CRITERIA.md`: summary source-type label contract 명시

## 검증
- `python3 -m py_compile core/agent_loop.py app/web.py` — 통과
- `make e2e-test` — `12 passed (2.8m)`
- `git diff --check` (변경 파일) — 통과

## 남은 리스크
- mock adapter 환경에서는 search mode가 실행되지 않으므로 `선택 결과 요약` label을 dedicated assertion으로 고정할 수 없음
- `문서 요약` label은 시나리오 1에서 간접적으로 확인 가능 (response에 evidence + summary_chunks가 있고 active_context.kind가 document)
- dirty worktree는 여전히 넓음 (이번 라운드에서 unrelated 변경을 건드리지 않음)
