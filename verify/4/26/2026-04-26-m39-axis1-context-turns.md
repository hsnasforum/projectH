STATUS: verified
CONTROL_SEQ: 225
BASED_ON_WORK: work/4/26/2026-04-26-review-queue-context-turns.md
VERIFIED_BY: Claude
NEXT_CONTROL: .pipeline/advisory_request.md CONTROL_SEQ 226

---

# 2026-04-26 M39 Axis 1 — Review Queue context_turns 검증

## 변경 파일 (이번 커밋 대상)
- `app/serializers.py` — `_extract_context_turns` helper + `context_turns` 항목 dict 포함
- `app/frontend/src/api/client.ts` — `ReviewQueueItem.context_turns` 필드 추가
- `app/frontend/src/components/ReviewQueuePanel.tsx` — `대화 맥락` 섹션 렌더링 (4개 참조)
- `tests/test_serializers.py` — `test_build_review_queue_items_includes_recent_context_turns` 신규
- `tests/test_web_app.py` — 기존 expected payload에 additive `context_turns` 반영
- `e2e/tests/web-smoke.spec.mjs` — review queue context payload + 렌더링 신규 smoke 추가
- `work/4/26/2026-04-26-review-queue-context-turns.md` (신규)

## 검증 요약
- `python3 -m py_compile app/serializers.py` — 통과
- `python3 -m unittest -v tests.test_serializers` — **3 tests OK** (신규 context_turns 테스트 포함)
- `python3 -m unittest -v tests.test_web_app.WebAppServiceTest.test_submit_candidate_confirmation_records_candidate_linked_trace_and_stays_separate_from_save_support` — **1 test OK**
- `cd app/frontend && npx tsc --noEmit` — 통과, 타입 오류 없음
- `python3 -m unittest -v tests.test_docs_sync` — **13 tests OK** (프로젝트 루트 기준)
- `node --check e2e/tests/web-smoke.spec.mjs` — 통과
- `git diff --check` 대상 파일 — 통과
- `npx playwright test -g "review queue"` — sandbox socket 제한으로 실행 불가 (코드 오류 아님)

## 확인한 내용
- `_extract_context_turns(source_message_id)` 헬퍼: `context_turns_limit=3`, `context_text_max=500`; casefold 비교로 source message 탐색; 이전 최대 3 turn을 `role`/`text`/`message_id`로 직렬화
- global review item: 빈 `context_turns: []` 반환
- `ReviewQueueItem` TypeScript 인터페이스: `context_turns?: Array<{role: string; text: string; message_id?: string|null}> | null`
- ReviewQueuePanel.tsx: `context_turns` 4개 참조 확인 (조건부 섹션 렌더링)
- 기존 review queue 시나리오 회귀 없음 (test_serializers, test_web_app 통과)

## 남은 리스크
- Playwright review queue 신규 E2E: sandbox 제약으로 실제 브라우저 미검증; non-sandbox 또는 CI 환경 확인 필요
- 전체 `make e2e-test` 미실행; M38 기준선 `150 passed`, 신규 시나리오 추가로 `151+` 예상
- 기존 미추적 아티팩트(`verify/4/25/...`, `report/gemini/**`)는 이번 범위 밖

## 다음 제어
- NEXT: `.pipeline/advisory_request.md` CONTROL_SEQ 226 — M39 Axis 2 방향 확인
