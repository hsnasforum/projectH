# 2026-04-26 review queue evidence summary

## 변경 파일
- `app/serializers.py`
- `app/frontend/src/api/client.ts`
- `app/frontend/src/components/ReviewQueuePanel.tsx`
- `tests/test_serializers.py`
- `tests/test_web_app.py`
- `work/4/26/2026-04-26-review-queue-evidence-summary.md`

## 사용 skill
- `doc-sync`: review queue UI/API 변경이 기존 문서 inventory 테스트를 깨지 않는지 확인했고, 추가 문서 변경이 필요하지 않음을 점검했습니다.
- `finalize-lite`: 변경 파일, 실행 검증, 미실행 범위, closeout 필요 여부를 점검했습니다.
- `work-log-closeout`: 실제 변경과 검증 결과를 이 `/work` closeout으로 정리했습니다.

## 변경 이유
- review queue item이 `supporting_artifact_ids`, `supporting_signal_refs`, `supporting_confirmation_refs`를 이미 내려 주지만, 운영자가 후보의 정량적 증거 강도를 바로 읽을 수 있는 요약 필드는 없었습니다.
- global 후보의 반복 세션 수는 `promotion_basis` 문자열에서 파싱해야 해 UI에서 직접 계산하기보다 서버 직렬화 단계에서 안정적으로 제공할 필요가 있었습니다.

## 핵심 변경
- `_build_review_queue_items`에 `evidence_summary` 계산 helper를 추가해 artifact/signal/confirmation/recurring session count를 item에 포함했습니다.
- durable candidate item은 기존 supporting 배열을 재사용해 summary를 만들고, 기존 배열 필드는 제거하거나 변경하지 않았습니다.
- global candidate item도 supporting artifact 수와 `cross_session_recurrence:N` 기반 반복 세션 수를 `evidence_summary`에 포함합니다.
- `ReviewQueueItem` TypeScript interface에 `evidence_summary` 타입을 추가했습니다.
- `ReviewQueuePanel`에 증거 요약 배지를 추가해 아티팩트/신호/확인 개수와 2개 이상 세션 반복 여부를 표시합니다.
- serializer unit test에 durable/global evidence summary 검증을 추가하고, 기존 web_app exact expected payload에 additive field를 반영했습니다.

## 검증
- `python3 -m py_compile app/serializers.py`
  - 통과, 출력 없음.
- `python3 -m unittest -v tests.test_serializers`
  - 통과.
  - `Ran 5 tests in 0.005s`
- `python3 -m unittest -v tests.test_web_app.WebAppServiceTest.test_submit_candidate_confirmation_records_candidate_linked_trace_and_stays_separate_from_save_support`
  - 통과.
  - `Ran 1 test in 0.032s`
- `cd app/frontend && npx tsc --noEmit`
  - 통과, 출력 없음.
- `python3 -m unittest -v tests.test_docs_sync`
  - 통과.
  - `Ran 13 tests in 0.024s`
- `git diff --check -- app/serializers.py app/frontend/src/api/client.ts app/frontend/src/components/ReviewQueuePanel.tsx tests/test_serializers.py tests/test_web_app.py`
  - 통과, 출력 없음.

## 남은 리스크
- 이번 handoff의 검증 범위에 browser smoke는 포함되지 않아 Playwright review queue flow는 실행하지 않았습니다.
- 전체 `make e2e-test`도 실행하지 않았습니다. 현재 환경은 앞선 round와 동일하게 app.web socket 생성이 제한될 가능성이 큽니다.
- 작업 전부터 있던 `verify/4/25/2026-04-25-m36-preference-pause-functional-e2e.md`, `report/gemini/**`, 기존 미추적 `work/4/25/2026-04-25-m31-bundle-publish-closeout.md` 등은 이번 범위가 아니라 건드리지 않았습니다.
- commit, push, branch/PR 생성, 다음 slice 선택은 수행하지 않았습니다.
