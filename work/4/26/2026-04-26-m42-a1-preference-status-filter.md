# 2026-04-26 M42 A1 preference status filter

## 변경 파일
- `app/handlers/preferences.py`
- `app/frontend/src/api/client.ts`
- `app/frontend/src/components/PreferencePanel.tsx`
- `docs/MILESTONES.md`
- `docs/PRODUCT_SPEC.md`
- `docs/ACCEPTANCE_CRITERIA.md`
- `tests/test_web_app.py`
- `work/4/26/2026-04-26-m42-a1-preference-status-filter.md`

## 사용 skill
- `finalize-lite`: 구현 후 통과한 검증과 완료되지 않은 검증을 분리해 마무리 범위를 확인했다.
- `release-check`: UI/payload/docs/test 변경의 확인 범위와 남은 리스크를 점검했다.
- `doc-sync`: PreferencePanel과 `/api/preferences` payload 계약을 milestone/spec/acceptance 문서에 맞췄다.
- `work-log-closeout`: 변경 파일, 실제 검증, 미완료 검증, 남은 리스크를 한국어 closeout으로 남겼다.

## 변경 이유
- M42 Axis 1 handoff는 PreferencePanel에서 candidate/active/paused 선호를 status별로 구분해서 볼 수 있게 하고, 서버 payload에 `paused_count`를 추가하도록 요구했다.
- 기존 activate/pause/reject API와 버튼 동작은 이미 구현되어 있었으므로 이번 라운드는 UI 필터, count payload, 문서/테스트 보강으로 제한했다.

## 핵심 변경
- 이미 구현되어 있던 기능은 유지했다: `/api/preferences/activate`, `/api/preferences/pause`, `activate_preference()`, `pause_preference()`, PreferencePanel의 activate/pause/reject 버튼, status 배지, `active_count`/`candidate_count` payload는 재구현하지 않았다.
- 이번 라운드에서 새로 추가한 기능: `list_preferences_payload()`가 `paused_count`를 반환한다.
- 이번 라운드에서 새로 추가한 기능: PreferencePanel이 rejected 항목 숨김을 유지한 채 전체/후보/활성/일시중지 탭과 탭별 count를 표시하고, 선택한 status만 목록에 렌더링한다.
- 이번 라운드에서 새로 추가한 기능: `PreferencesPayload` TypeScript 타입에 `paused_count`를 반영했다.
- 이번 라운드에서 새로 추가한 문서: M42 milestone과 Next 3 Priorities를 갱신하고, 제품 spec/acceptance의 preference payload/UI 계약을 현재 구현에 맞췄다.
- 이번 라운드에서 새로 추가한 테스트: `tests.test_web_app.WebAppServiceTest.test_list_preferences_payload_includes_status_counts`가 candidate/active/paused count를 고정한다.

## 검증
- `sha256sum .pipeline/implement_handoff.md` 확인: `f5db4c8d883dfd97fcae0606582492c5ea93811410bc45abdb244307c5ddad3f`로 요청 handoff SHA와 일치.
- `python3 -m py_compile app/handlers/preferences.py` 통과, 출력 없음.
- `python3 -m unittest -v tests.test_web_app.WebAppServiceTest.test_list_preferences_payload_includes_status_counts` 통과.
  - `Ran 1 test in 0.010s`
- `timeout 30s python3 -m unittest -v tests.test_web_app.WebAppServiceTest.test_handle_chat_external_fact_colloquial_info_questions_use_web_search_when_enabled` 통과.
  - `Ran 1 test in 18.579s`
- `cd app/frontend && npx tsc --noEmit` 통과, 출력 없음.
- `git diff --check -- app/handlers/preferences.py app/frontend/src/components/PreferencePanel.tsx app/frontend/src/api/client.ts docs/MILESTONES.md docs/PRODUCT_SPEC.md docs/ACCEPTANCE_CRITERIA.md tests/test_web_app.py work/4/26/2026-04-26-m42-a1-preference-status-filter.md` 통과, 출력 없음.
- `python3 -m unittest -v tests.test_web_app`는 실행했지만 완료 결과를 얻지 못했다. 여러 테스트가 통과한 뒤 `test_handle_chat_external_fact_colloquial_info_questions_use_web_search_when_enabled` 구간에서 장시간 반환되지 않아, 이 전체 스위트는 통과로 계산하지 않는다.
- Playwright/browser E2E는 handoff의 sandbox 제약 기준에 따라 실행하지 않았다.

## 남은 리스크
- 전체 `tests.test_web_app` 완료 결과가 없어, 새 status-count 회귀와 타입 체크는 확인됐지만 웹앱 전체 회귀 통과는 아직 검증되지 않았다.
- 브라우저에서 PreferencePanel 탭의 실제 클릭 동작은 Playwright로 확인하지 않았다. 이번 라운드는 TypeScript 타입 체크와 단위 테스트로 대체했다.
- 기존 작업트리의 untracked `report/gemini/**` 파일들은 이번 handoff 범위 밖이므로 보존하고 수정하지 않았다.
- commit, push, branch/PR 생성, merge는 수행하지 않았다.
