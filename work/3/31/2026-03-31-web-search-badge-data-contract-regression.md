# 2026-03-31 web-search badge data contract service regression 

## 변경 파일
- `tests/test_web_app.py`

## 사용 skill
- 없음

## 변경 이유
- `.pipeline/codex_feedback.md`가 `STATUS: implement`로 web-search history badge data contract에 대한 backend/service regression 1개 추가를 지시.
- 기존 browser smoke (scenario 15)는 frontend rendering만 보호하며, `WebSearchStore.save()` → `list_session_record_summaries()` 직렬화 경로의 `answer_mode`, `verification_label`, `source_roles` exact field 보존은 service test 축에서 미보호 상태였음.
- 근거: `work/3/31/2026-03-31-web-search-history-badge-smoke-verification.md`, `verify/3/31/2026-03-31-web-search-history-badge-smoke-truth-check.md`

## 핵심 변경
- `test_web_search_store_badge_data_contract_serializes_exact_fields` 추가
  - `WebSearchStore.save()`로 3개 record 저장: `entity_card`, `latest_update`, `general` (response_origin=None fallback)
  - `list_session_record_summaries()`에서 query 기준 매칭 후:
    - `entity_card`: `answer_mode="entity_card"`, `verification_label="공식+기사 교차 확인"`, `source_roles=["공식 기반", "보조 기사"]`
    - `latest_update`: `answer_mode="latest_update"`, `verification_label="설명형 단일 출처"`, `source_roles=["설명형 출처"]`
    - `general` (no response_origin): `answer_mode="general"`, `verification_label=""`, `source_roles=[]`
- `storage.web_search_store.WebSearchStore` import 추가
- UI, Playwright smoke, docs, approval flow, reviewed-memory 변경 없음

## 검증
- `python3 -m unittest -v tests.test_web_app`: 99 tests, OK (1.768s)
- `git diff --check -- tests/test_web_app.py app/web.py storage/web_search_store.py core/agent_loop.py README.md docs/ACCEPTANCE_CRITERIA.md docs/MILESTONES.md docs/TASK_BACKLOG.md`: 통과

## 남은 리스크
- 이 test는 `WebSearchStore` 직접 호출 경로만 보호함. `handle_chat` → investigation pipeline → `WebSearchStore.save()` 사이에서 `response_origin` field가 누락/변환되는 경로는 별도 integration test 필요.
- dirty worktree가 여전히 넓음.
