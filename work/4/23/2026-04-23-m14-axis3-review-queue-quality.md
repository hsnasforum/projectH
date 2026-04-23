# 2026-04-23 M14 Axis 3 review queue quality

## 변경 파일
- `app/serializers.py`
- `app/frontend/src/api/client.ts`
- `app/frontend/src/types.ts`
- `app/frontend/src/hooks/useChat.ts`
- `app/frontend/src/components/ChatArea.tsx`
- `app/frontend/src/App.tsx`
- `tests/test_serializers.py`
- `tests/test_web_app.py`
- `docs/MILESTONES.md`
- `work/4/23/2026-04-23-m14-axis3-review-queue-quality.md`

## 사용 skill
- `doc-sync`: M14 Axis 3 shipped 기록을 현재 구현 범위에 맞춰 `docs/MILESTONES.md`에만 반영했습니다.
- `finalize-lite`: handoff acceptance 검증, 추가 focused regression, TypeScript 검증, 남은 미검증 범위를 점검했습니다.
- `work-log-closeout`: 실제 변경 파일과 실행 결과를 `/work` 형식에 맞춰 기록했습니다.

## 변경 이유
- handoff는 advisory seq 29 기준 M14 Axis 3 review queue quality integration을 요청했습니다.
- M14 Axis 2에서 preference panel에는 quality surface가 추가되었지만, review queue item serializer와 기존 `리뷰 N건` badge에는 correction `similarity_score` 기반 quality 정보가 없었습니다.
- 목표는 새 패널을 만들지 않고 기존 review badge에 `고품질 N건` count만 표시하는 것입니다.

## 핵심 변경
- `_build_review_queue_items()`가 각 review queue item의 `artifact_id`로 `correction_store.find_by_artifact()`를 조회하고, correction `similarity_score` 평균을 `quality_info.avg_similarity_score`로 직렬화합니다.
- 평균 점수가 있으면 `core.delta_analysis.is_high_quality()` 기준으로 `quality_info.is_high_quality`를 설정하고, correction이 없으면 두 값을 `None`으로 유지합니다.
- frontend에 `ReviewQueueItem` 타입을 추가하고 `Session.review_queue_items`를 해당 타입으로 좁혔습니다.
- `useChat`이 `highQualityReviewCount`를 session load와 stream final merge 양쪽에서 계산하고, `App.tsx`가 `ChatArea`로 전달합니다.
- `ChatArea.tsx`의 기존 `리뷰 N건` badge 안에 high-quality item이 있을 때만 `고품질 N건` 보조 count를 표시합니다.
- serializer 단위 테스트를 추가하고, 기존 exact-shape 웹 테스트의 review queue expected dict에 새 `quality_info` 키를 반영했습니다.

## 검증
- `python3 -m py_compile app/serializers.py`
  - 통과: 출력 없음
- `python3 -m unittest tests.test_serializers -v`
  - 1차 실패: 테스트 stub에 production `WebAppService` helper인 `_normalize_optional_text`가 없어 `AttributeError` 발생
  - 수정 후 통과: `2 tests`
- `cd app/frontend && npx tsc --noEmit`
  - 통과: 출력 없음
- `git diff --check -- app/serializers.py docs/MILESTONES.md`
  - 통과: 출력 없음
- `git diff --check -- app/serializers.py docs/MILESTONES.md app/frontend/src/api/client.ts app/frontend/src/types.ts app/frontend/src/hooks/useChat.ts app/frontend/src/components/ChatArea.tsx app/frontend/src/App.tsx tests/test_serializers.py tests/test_web_app.py`
  - 통과: 출력 없음
- `python3 -m unittest tests.test_web_app.WebAppServiceTest.test_submit_candidate_confirmation_records_candidate_linked_trace_and_stays_separate_from_save_support -v`
  - 통과: `1 test`

## 남은 리스크
- 전체 test suite와 Playwright browser smoke는 실행하지 않았습니다.
- badge UI는 TypeScript compile로만 확인했고, 실제 브라우저 스크린샷 검증은 이번 handoff acceptance 범위에 없어서 실행하지 않았습니다.
- SQLite quality parity와 별도 review queue panel/list rendering은 handoff boundary에 따라 제외했습니다.
