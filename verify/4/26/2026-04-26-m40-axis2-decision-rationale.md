STATUS: verified
CONTROL_SEQ: 237
BASED_ON_WORK: work/4/26/2026-04-26-review-decision-rationale.md
VERIFIED_BY: Claude
NEXT_CONTROL: .pipeline/advisory_request.md CONTROL_SEQ 238

---

# 2026-04-26 M40 Axis 2 — review decision rationale capture 검증

## 변경 파일 (이번 커밋 대상)
- `app/handlers/aggregate.py` — global ACCEPT/REJECT `source_refs`에 `reason_note` 조건부 추가
- `app/frontend/src/api/client.ts` — `postCandidateReview`에 `reasonNote?: string` 추가
- `app/frontend/src/components/ReviewQueuePanel.tsx` — 선택적 rationale textarea + 전달
- `app/frontend/src/App.tsx` — callback 시그니처 bridge (3줄, 최소 범위)
- `app/frontend/src/components/Sidebar.tsx` — callback 시그니처 bridge (1줄, 최소 범위)
- `tests/test_web_app.py` — global candidate reason_note 저장 + reject 미전달 신규 테스트
- `work/4/26/2026-04-26-review-decision-rationale.md` (신규)

## 검증 요약
- `python3 -m py_compile app/handlers/aggregate.py` — 통과
- `test_web_app.test_submit_global_candidate_review_source_refs_include_optional_reason_note` — **1 test OK** (신규)
- `test_web_app.test_submit_candidate_confirmation_records_...` — **1 test OK** (기존 회귀)
- `cd app/frontend && npx tsc --noEmit` — 통과 (exit 0)
- `python3 -m unittest -v tests.test_docs_sync` — **13 tests OK**
- `git diff --check` 6개 파일 — 통과

## 확인한 내용
- `aggregate.py` global ACCEPT/REJECT `source_refs`: `**({"reason_note": reason_note} if reason_note else {})` 2곳 추가 확인
- durable candidate path(`line 273`)는 이미 처리됨 — 미수정 확인
- `postCandidateReview`: `reasonNote` 파라미터 추가, `reason_note` 조건부 포함 확인
- App.tsx(3줄)/Sidebar.tsx(1줄): callback bridge 최소 변경으로 panel → API 전달 연결
- browser/E2E: sandbox 제약으로 미실행 (일관 위험)

## 범위 노트
- `App.tsx`와 `Sidebar.tsx`는 handoff 명시 파일 외이나 `ReviewQueuePanel` → `postCandidateReview` 전달에 필수 callback bridge로 함께 변경; 변경 규모 최소(총 4줄) 확인

## 남은 리스크
- browser E2E 미검증; 전체 `make e2e-test` 미실행
- M40 doc-sync (MILESTONES.md M40 완료 기록) 미수행
- M41 방향 미확정

## 다음 제어
- NEXT: `.pipeline/advisory_request.md` CONTROL_SEQ 238 — M40 closure 확인 + 다음 방향 (doc-sync Axis 3 또는 M41 direction)
