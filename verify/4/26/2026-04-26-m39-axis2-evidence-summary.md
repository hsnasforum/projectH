STATUS: verified
CONTROL_SEQ: 228
BASED_ON_WORK: work/4/26/2026-04-26-review-queue-evidence-summary.md
VERIFIED_BY: Claude
NEXT_CONTROL: .pipeline/advisory_request.md CONTROL_SEQ 229

---

# 2026-04-26 M39 Axis 2 — review queue evidence_summary 검증

## 변경 파일 (이번 커밋 대상)
- `app/serializers.py` — `_parse_recurring_session_count` + `_build_evidence_summary` helper; durable/global item에 `evidence_summary` 포함
- `app/frontend/src/api/client.ts` — `ReviewQueueItem.evidence_summary` 필드 추가
- `app/frontend/src/components/ReviewQueuePanel.tsx` — 증거 배지/카운트 표시
- `tests/test_serializers.py` — durable/global evidence_summary 신규 단위 테스트 2개
- `tests/test_web_app.py` — 기존 expected payload에 additive evidence_summary 반영
- `work/4/26/2026-04-26-review-queue-evidence-summary.md` (신규)

## 검증 요약
- `python3 -m py_compile app/serializers.py` — 통과
- `python3 -m unittest -v tests.test_serializers` — **5 tests OK** (신규 2개: evidence_summary durable/global)
- `test_web_app` 특정 테스트 — **1 test OK**
- `cd app/frontend && npx tsc --noEmit` — 통과
- `python3 -m unittest -v tests.test_docs_sync` — **13 tests OK** (프로젝트 루트 기준)
- `git diff --check` 5개 파일 — 통과

## 확인한 내용
- `_parse_recurring_session_count`: `"cross_session_recurrence:N"` 패턴에서 N 안전 파싱
- `_build_evidence_summary`: `artifact_count`/`signal_count`/`confirmation_count`/`recurring_session_count` 계산; durable + global 양쪽에 적용
- `ReviewQueueItem.evidence_summary?: {artifact_count, signal_count, confirmation_count, recurring_session_count} | null` 타입 확인
- 기존 `supporting_artifact_ids[]` 등 배열 필드 제거/수정 없음 (additive only)
- Playwright review queue browser smoke: sandbox socket 제한으로 미실행 (이전 round와 동일)

## M39 완료 상태
- **Axis 1**: `context_turns` — 대화 맥락 직전 3턴 직렬화 (commit `774dbe1`)
- **Axis 2**: `evidence_summary` — 아티팩트/신호/반복세션 수 정량화 (이번 커밋)
- **잔여 위험**: 브라우저 E2E 미검증 (sandbox 제약 지속); 전체 `make e2e-test` 미실행

## 다음 제어
- NEXT: `.pipeline/advisory_request.md` CONTROL_SEQ 229 — M39 closure 확인 + M40 direction
