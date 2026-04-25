STATUS: verified
CONTROL_SEQ: 234
BASED_ON_WORK: work/4/26/2026-04-26-review-queue-source-session.md
VERIFIED_BY: Claude
NEXT_CONTROL: .pipeline/advisory_request.md CONTROL_SEQ 235

---

# 2026-04-26 M40 Axis 1 — review queue source_session 검증

## 변경 파일 (이번 커밋 대상)
- `app/serializers.py` — `_serialize_session`에서 session_id/title 추출 → `_build_review_queue_items` 전달; durable + global item에 `source_session_id`/`source_session_title` 포함
- `app/frontend/src/api/client.ts` — `ReviewQueueItem.source_session_id?`, `source_session_title?` 추가
- `app/frontend/src/components/ReviewQueuePanel.tsx` — `세션: {title}` 조건부 라벨 표시
- `tests/test_serializers.py` — `test_build_review_queue_items_includes_source_session_metadata` 신규
- `tests/test_web_app.py` — 기존 expected payload에 additive 필드 반영
- `work/4/26/2026-04-26-review-queue-source-session.md` (신규)

## 검증 요약
- `python3 -m py_compile app/serializers.py` — 통과
- `python3 -m unittest -v tests.test_serializers` — **6 tests OK** (신규: source_session_metadata)
- `test_web_app` 지정 테스트 — **1 test OK**
- `cd app/frontend && npx tsc --noEmit` — 통과 (exit 0)
- `python3 -m unittest -v tests.test_docs_sync` — **13 tests OK**
- `git diff --check` 5개 파일 — 통과

## 확인한 내용
- `session.get("session_id")` + `session.get("title")` → keyword args로 `_build_review_queue_items` 전달 확인
- durable item: `"source_session_id": session_id, "source_session_title": session_title` 2회 추가 (durable + global) 확인
- TypeScript: `source_session_id?: string | null; source_session_title?: string | null;` 추가 확인
- 기존 `context_turns`, `evidence_summary` 등 M39 필드 변경 없음 (additive only)
- browser/E2E: sandbox 제약으로 미실행 (이전 라운드와 동일)

## 남은 리스크
- browser E2E 미검증; 전체 `make e2e-test` 미실행
- M40 Axis 2 (Decision rationale capture) 구현 범위 미확정

## 다음 제어
- NEXT: `.pipeline/advisory_request.md` CONTROL_SEQ 235 — M40 Axis 2 Decision rationale capture 구체적 slice 확정
