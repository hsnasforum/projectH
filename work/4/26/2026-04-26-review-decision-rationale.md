# 2026-04-26 review decision rationale

## 변경 파일
- `app/handlers/aggregate.py`
- `app/frontend/src/api/client.ts`
- `app/frontend/src/App.tsx`
- `app/frontend/src/components/Sidebar.tsx`
- `app/frontend/src/components/ReviewQueuePanel.tsx`
- `tests/test_web_app.py`
- `work/4/26/2026-04-26-review-decision-rationale.md`

## 사용 skill
- `finalize-lite`: 변경 파일, 실행 검증, 미실행 범위, closeout 필요 여부를 점검했습니다.
- `doc-sync`: UI/payload 변경에 따른 문서 동기화 필요 여부를 확인했고, handoff bounded behavior 밖 문서 변경은 하지 않았습니다.
- `work-log-closeout`: 실제 변경과 검증 결과를 이 `/work` closeout으로 정리했습니다.

## 변경 이유
- M40 Axis 2 handoff에서 review queue 후보 수락/거절 시 선택적 사유(`reason_note`)를 프론트엔드에서 API로 전달하고, global candidate path의 Preference `source_refs`에도 남기도록 요구했습니다.
- durable candidate path는 이미 `reason_note`를 `candidate_review_record`에 저장하므로 해당 경로는 수정하지 않았습니다.

## 핵심 변경
- `postCandidateReview`에 `reasonNote?: string` 인자를 추가하고, 값이 있을 때만 요청 body에 `reason_note`를 포함했습니다.
- `ReviewQueuePanel`에 항목별 선택 사유 textarea를 추가하고, 수락/거절 액션에만 trimmed `reasonNote`를 전달했습니다.
- `App.tsx`와 `Sidebar.tsx`의 callback 시그니처를 맞춰 panel 입력값이 API client까지 전달되게 했습니다.
- `app/handlers/aggregate.py`의 global ACCEPT/REJECT `source_refs`에 `reason_note` 조건부 추가를 반영했습니다.
- `tests/test_web_app.py`에 global candidate accept는 `reason_note`를 저장하고, reject 미전달 케이스는 필드를 만들지 않는 회귀 테스트를 추가했습니다.

## 검증
- `python3 -m py_compile app/handlers/aggregate.py`
  - 통과, 출력 없음.
- `python3 -m unittest -v tests.test_web_app.WebAppServiceTest.test_submit_global_candidate_review_source_refs_include_optional_reason_note`
  - 통과.
  - `Ran 1 test in 0.006s`
- `python3 -m unittest -v tests.test_web_app.WebAppServiceTest.test_submit_candidate_confirmation_records_candidate_linked_trace_and_stays_separate_from_save_support`
  - 통과.
  - `Ran 1 test in 0.031s`
- `cd app/frontend && npx tsc --noEmit`
  - 통과, 출력 없음.
- `python3 -m unittest -v tests.test_docs_sync`
  - 통과.
  - `Ran 13 tests in 0.034s`
- `git diff --check -- app/handlers/aggregate.py app/frontend/src/api/client.ts app/frontend/src/App.tsx app/frontend/src/components/Sidebar.tsx app/frontend/src/components/ReviewQueuePanel.tsx tests/test_web_app.py`
  - 통과, 출력 없음.

## 남은 리스크
- handoff 지정 검증에 browser/E2E는 포함되지 않아 실제 브라우저 smoke는 실행하지 않았습니다.
- UI/payload 변경이지만 제품 문서는 이번 implement handoff 범위에 포함되지 않아 수정하지 않았고, `tests.test_docs_sync`만 확인했습니다.
- `App.tsx`와 `Sidebar.tsx`는 handoff bounded list에 명시되지는 않았지만, `ReviewQueuePanel`의 사유 입력값을 `postCandidateReview`까지 전달하는 필수 callback bridge라 함께 수정했습니다.
- 작업 전부터 있던 `verify/4/25/2026-04-25-m36-preference-pause-functional-e2e.md`, `report/gemini/**`, `work/4/25/2026-04-25-m31-bundle-publish-closeout.md` 변경/미추적 항목은 이번 범위가 아니라 건드리지 않았습니다.
- commit, push, branch/PR 생성, 다음 slice 선택은 수행하지 않았습니다.
