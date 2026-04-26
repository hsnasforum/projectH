# 2026-04-26 M43 A2 transition visibility

## 변경 파일
- `app/handlers/preferences.py`
- `app/frontend/src/api/client.ts`
- `app/frontend/src/components/PreferencePanel.tsx`
- `tests/test_web_app.py`

## 사용 skill
- `security-gate`: task log를 읽어 preference UI payload에 노출하는 변경의 로컬 읽기 경계와 승인 영향 여부를 확인했다.
- `finalize-lite`: 구현 후 실행한 검증, 미실행 검증, doc-sync 보류 범위, closeout 준비 상태를 점검했다.
- `release-check`: 변경 파일과 실제 검증 결과가 handoff 범위에 맞는지 확인했다.
- `doc-sync`: UI/API 계약 변경은 문서 동기화 대상이지만 이번 handoff가 docs 변경을 별도 라운드로 제한했음을 확인했다.
- `work-log-closeout`: 변경 파일, 실제 검증, 남은 리스크를 한국어 closeout으로 정리했다.

## 변경 이유
- M43 Axis 1에서 preference 상태 전환의 선택적 `transition_reason`을 task log에 기록하기 시작했다.
- M43 Axis 2는 preference store 스키마를 바꾸지 않고, `list_preferences_payload()`가 task log를 읽어 최신 전환 이유를 `last_transition_reason`으로 UI에 제공하도록 요구했다.

## 핵심 변경
- `app/handlers/preferences.py:178` 부근, `conflict_info` enrichment 루프와 payload `return` 사이에 task log `system` records 읽기 블록을 추가했다.
- `preference_activated`, `preference_paused`, `preference_rejected` task log 중 `transition_reason`이 있는 최신 record를 preference별로 추적하고, 일치하는 preference payload에 `last_transition_reason`을 추가했다.
- `app/frontend/src/api/client.ts:220`에 `PreferenceRecord.last_transition_reason?: string | null` 타입을 추가했다.
- `app/frontend/src/components/PreferencePanel.tsx:266`에서 `lastTransitionReason`을 정규화하고, `app/frontend/src/components/PreferencePanel.tsx:382` 부근에서 값이 있을 때만 `전환 이유: ...`를 렌더링한다.
- 기존 activate/pause/reject 버튼, conflict confirm, reject fade-out, `review_reason_note` audit block은 변경하지 않았다.
- `tests/test_web_app.py:6380`에 `test_list_preferences_payload_includes_last_transition_reason`을 추가해 reason 있는 preference의 payload 노출과 reason 없는 preference의 키 부재를 함께 확인했다.

## 검증
- `sha256sum .pipeline/implement_handoff.md` 확인: `391b95e52fe8c22027c32bd40d9ad554e4e6821fac745031f023e5c2f2a16421`로 요청 handoff SHA와 일치.
- `python3 -m py_compile app/handlers/preferences.py` 통과, 출력 없음.
- `cd app/frontend && npx tsc --noEmit` 통과, 출력 없음.
- `python3 -m unittest -v tests.test_web_app.WebAppServiceTest.test_list_preferences_payload_includes_last_transition_reason` 통과.
  - `Ran 1 test in 0.005s`
- `git diff --check -- app/handlers/preferences.py app/frontend/src/api/client.ts app/frontend/src/components/PreferencePanel.tsx tests/test_web_app.py` 통과, 출력 없음.
- `git diff -- app/handlers/preferences.py app/frontend/src/api/client.ts app/frontend/src/components/PreferencePanel.tsx tests/test_web_app.py`로 변경 범위가 handoff의 네 파일에 해당함을 확인했다.
- `git diff --check -- app/handlers/preferences.py app/frontend/src/api/client.ts app/frontend/src/components/PreferencePanel.tsx tests/test_web_app.py work/4/26/2026-04-26-m43-a2-transition-visibility.md` 통과, 출력 없음.

## 남은 리스크
- browser/Playwright로 실제 PreferencePanel 표시를 확인하지 않았다. 이번 handoff 검증 범위는 TypeScript 타입 체크와 handler 단위 테스트였다.
- 전체 `tests.test_web_app`, 전체 frontend test suite, release gate는 실행하지 않았다.
- UI/API 계약 변경은 `docs/PRODUCT_SPEC.md`, `docs/ARCHITECTURE.md`, `docs/ACCEPTANCE_CRITERIA.md` doc-sync 후보지만, 이번 handoff가 `docs/` 변경을 별도 doc-sync 라운드로 제한해 수정하지 않았다.
- security-gate 결과: 변경은 로컬 task log 읽기 및 payload/UI 노출에 한정되며, 새 persistence schema, 파일 write/overwrite/delete, approval bypass, 외부 네트워크, search/session schema 변경은 없다. rollback은 `last_transition_reason` enrichment, 타입/UI 렌더링, 신규 테스트를 되돌리는 방식으로 가능하다.
- 기존 작업트리의 untracked `report/gemini/**`, `verify/4/26/2026-04-26-b1-release-gate-pr35-reconcile.md`, `work/4/26/2026-04-26-pr36-release-gate-merge.md`는 이번 handoff 범위 밖이므로 수정하지 않았다.
- commit, push, branch/PR 생성, merge는 수행하지 않았다.
