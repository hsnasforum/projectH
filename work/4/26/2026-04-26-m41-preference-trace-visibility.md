# 2026-04-26 m41 preference trace visibility

## 변경 파일
- `app/handlers/aggregate.py`
- `app/handlers/preferences.py`
- `app/frontend/src/api/client.ts`
- `app/frontend/src/components/PreferencePanel.tsx`
- `tests/test_web_app.py`
- `work/4/26/2026-04-26-m41-preference-trace-visibility.md`

## 사용 skill
- `finalize-lite`: 변경 파일, 실행 검증, 미실행 범위, closeout 필요 여부를 점검했습니다.
- `doc-sync`: UI/payload 변경에 따른 문서 동기화 필요 여부를 확인했고, handoff bounded files 밖 문서 변경은 하지 않았습니다.
- `work-log-closeout`: 실제 변경과 검증 결과를 이 `/work` closeout으로 정리했습니다.

## 변경 이유
- M41 Axis 1 handoff에서 M40에서 캡처한 결정 사유(`reason_note`)와 출처 세션 제목(`session_title`)을 Preference 저장 경로와 PreferencePanel 표시까지 연결하도록 요구했습니다.
- 기존 preference payload는 `reviewed_candidate_source_refs` 내부 값을 top-level audit 필드로 노출하지 않아 PreferencePanel에서 감사 추적 정보를 표시할 수 없었습니다.

## 핵심 변경
- global candidate ACCEPT/REJECT `source_refs`에 `session_title`을 조건부로 추가했습니다.
- durable candidate ACCEPT `source_refs`에 `reason_note`와 `session_title`을 조건부로 추가했습니다.
- `list_preferences_payload`가 기존 `reviewed_candidate_source_refs` 배열에서 감사 ref를 읽어 `review_reason_note`, `source_session_title`을 top-level로 노출하도록 했습니다.
- frontend `PreferenceRecord` 타입에 `review_reason_note`, `source_session_title`을 추가했습니다.
- `PreferencePanel`에서 값이 있을 때만 `출처 세션`과 `결정 사유` audit block을 표시하도록 했습니다.
- web app 회귀 테스트에서 global/durable preference source ref 저장과 payload 노출을 확인했습니다.

## 검증
- `python3 -m py_compile app/handlers/aggregate.py app/handlers/preferences.py`
  - 통과, 출력 없음.
- `python3 -m unittest -v tests.test_web_app.WebAppServiceTest.test_submit_global_candidate_review_source_refs_include_optional_reason_note`
  - 통과.
  - `Ran 1 test in 0.013s`
- `python3 -m unittest -v tests.test_web_app.WebAppServiceTest.test_submit_candidate_review_accept_persists_local_preference_candidate`
  - 통과.
  - `Ran 1 test in 0.043s`
- `python3 -m unittest -v tests.test_web_app.WebAppServiceTest.test_submit_candidate_confirmation_records_candidate_linked_trace_and_stays_separate_from_save_support`
  - 통과.
  - `Ran 1 test in 0.037s`
- `cd app/frontend && npx tsc --noEmit`
  - 통과, 출력 없음.
- `python3 -m unittest -v tests.test_docs_sync`
  - 통과.
  - `Ran 13 tests in 0.027s`
- `git diff --check -- app/handlers/aggregate.py app/handlers/preferences.py app/frontend/src/api/client.ts app/frontend/src/components/PreferencePanel.tsx tests/test_web_app.py`
  - 통과, 출력 없음.

## 남은 리스크
- handoff 지정 검증에 browser/E2E는 포함되지 않아 실제 PreferencePanel 렌더링 smoke는 실행하지 않았습니다.
- UI/payload 변경이지만 제품 문서는 이번 implement handoff 범위에 포함되지 않아 수정하지 않았고, `tests.test_docs_sync`만 확인했습니다.
- preference store 스키마(SQLite/JSON)는 수정하지 않았고 기존 `reviewed_candidate_source_refs`에 저장된 dict만 사용했습니다.
- 작업 전부터 있던 `verify/4/25/2026-04-25-m36-preference-pause-functional-e2e.md`, `report/gemini/**`, `work/4/25/2026-04-25-m31-bundle-publish-closeout.md` 변경/미추적 항목은 이번 범위가 아니라 건드리지 않았습니다.
- commit, push, branch/PR 생성, 다음 slice 선택은 수행하지 않았습니다.
