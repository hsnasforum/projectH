# 2026-04-26 review queue source session

## 변경 파일
- `app/serializers.py`
- `app/frontend/src/api/client.ts`
- `app/frontend/src/components/ReviewQueuePanel.tsx`
- `tests/test_serializers.py`
- `tests/test_web_app.py`
- `work/4/26/2026-04-26-review-queue-source-session.md`

## 사용 skill
- `finalize-lite`: 변경 파일, 실행 검증, 미실행 범위, closeout 필요 여부를 점검했습니다.
- `doc-sync`: UI/payload 변경에 따른 문서 동기화 필요 여부를 확인했고, handoff bounded files 밖 문서 변경은 하지 않았습니다.
- `work-log-closeout`: 실제 변경과 검증 결과를 이 `/work` closeout으로 정리했습니다.

## 변경 이유
- M40 Review Auditability slice에서 review queue 후보가 어느 세션 대화에서 나왔는지 운영자가 확인할 수 있어야 했습니다.
- 기존 review queue 항목은 `source_message_id`만 노출해 같은 후보의 세션 출처를 UI에서 직접 확인하기 어려웠습니다.

## 핵심 변경
- `SerializerMixin._serialize_session`에서 현재 session의 `session_id`와 `title`을 정규화해 `_build_review_queue_items`에 전달했습니다.
- durable review queue item과 global review queue item payload에 `source_session_id`, `source_session_title`을 additive 필드로 추가했습니다.
- frontend `ReviewQueueItem` 타입에 source session 필드를 추가했습니다.
- `ReviewQueuePanel`에서 `source_session_title`이 있을 때만 `세션: ...` 라벨을 표시하도록 했습니다.
- serializer 단위 테스트와 web app 단일 payload 기대값에 source session 필드를 추가했습니다.
- 기존 `ReviewQueueItem` 필드, `context_turns`, `evidence_summary` 구조는 변경하지 않았습니다.

## 검증
- `python3 -m py_compile app/serializers.py`
  - 통과, 출력 없음.
- `python3 -m unittest -v tests.test_serializers`
  - 통과.
  - `Ran 6 tests in 0.003s`
- `python3 -m unittest -v tests.test_web_app.WebAppServiceTest.test_submit_candidate_confirmation_records_candidate_linked_trace_and_stays_separate_from_save_support`
  - 통과.
  - `Ran 1 test in 0.038s`
- `cd app/frontend && npx tsc --noEmit`
  - 통과, 출력 없음.
- `python3 -m unittest -v tests.test_docs_sync`
  - 통과.
  - `Ran 13 tests in 0.024s`
- `git diff --check -- app/serializers.py app/frontend/src/api/client.ts app/frontend/src/components/ReviewQueuePanel.tsx tests/test_serializers.py tests/test_web_app.py`
  - 통과, 출력 없음.

## 남은 리스크
- handoff 지정 범위와 검증에 browser/E2E 실행은 포함되지 않아 실제 브라우저 smoke는 실행하지 않았습니다.
- UI/payload 변경이지만 handoff bounded files 밖의 제품 문서는 수정하지 않았고, `tests.test_docs_sync`만 확인했습니다.
- 작업 전부터 있던 `verify/4/25/2026-04-25-m36-preference-pause-functional-e2e.md`, `report/gemini/**`, `work/4/25/2026-04-25-m31-bundle-publish-closeout.md` 변경/미추적 항목은 이번 범위가 아니라 건드리지 않았습니다.
- commit, push, branch/PR 생성, 다음 slice 선택은 수행하지 않았습니다.
