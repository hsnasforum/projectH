STATUS: verified
CONTROL_SEQ: 243
BASED_ON_WORK: work/4/26/2026-04-26-m41-preference-trace-visibility.md
VERIFIED_BY: Claude
NEXT_CONTROL: .pipeline/implement_handoff.md CONTROL_SEQ 244

---

# 2026-04-26 M41 Axis 1 — Preference trace visibility 검증

## 변경 파일 (이번 커밋 대상)
- `app/handlers/aggregate.py` — global ACCEPT/REJECT에 `session_title`; durable ACCEPT에 `reason_note`+`session_title` 추가
- `app/handlers/preferences.py` — `reviewed_candidate_source_refs` / `source_refs` 읽어 `review_reason_note`/`source_session_title` top-level 노출
- `app/frontend/src/api/client.ts` — `PreferenceRecord.review_reason_note?`, `.source_session_title?` 추가
- `app/frontend/src/components/PreferencePanel.tsx` — `출처 세션` / `결정 사유` 조건부 audit block
- `tests/test_web_app.py` — global source_refs + durable accept 신규 테스트 커버리지
- `work/4/26/2026-04-26-m41-preference-trace-visibility.md` (신규)

## 검증 요약
- `python3 -m py_compile app/handlers/aggregate.py app/handlers/preferences.py` — 통과
- `test_submit_global_candidate_review_source_refs_include_optional_reason_note` — **1 test OK**
- `test_submit_candidate_review_accept_persists_local_preference_candidate` — **1 test OK**
- `test_submit_candidate_confirmation_records_...` — **1 test OK** (회귀)
- `cd app/frontend && npx tsc --noEmit` — 통과 (exit 0)
- `python3 -m unittest -v tests.test_docs_sync` — **13 tests OK**
- `git diff --check` 5개 파일 — 통과

## 확인한 내용
- `aggregate.py`: global path 3곳(ACCEPT×1 + REJECT×1 at global, durable ACCEPT×1)에 `session_title` / `reason_note` 조건부 추가 확인
- `preferences.py`: `reviewed_candidate_source_refs`(배열) 우선 → `source_refs`(dict) 폴백으로 audit ref 읽기; `review_reason_note`/`source_session_title` top-level 노출 확인
- TypeScript: `PreferenceRecord` 두 필드 추가, tsc 통과
- browser/E2E: sandbox 제약으로 미실행 (일관 위험)

## 오늘 docs-only 라운드 카운트
- Round 1: M39 Axis 3 (2026-04-26) ✓
- Round 2: M40 Axis 3 (2026-04-26) ✓
- Round 3 (다음): M41 Axis 2 doc-sync → "3+ 동일 패밀리 docs-only" 규칙 적용 직전

## 다음 제어 결정 근거
- M41 doc-sync(MILESTONES.md)는 M38/M39/M40 Axis 3와 동일 패턴; 모호성 없음
- 3번째 docs-only 라운드 직전 → 규칙에 따라 "bounded docs bundle"을 advisory 없이 직접 implement
- M41 doc-sync 완료 후 M42 방향은 별도 advisory 요청

## 다음 제어
- NEXT: `.pipeline/implement_handoff.md` CONTROL_SEQ 244 — M41 Axis 2 doc-sync (MILESTONES.md M41 closure)
