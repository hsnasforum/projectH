# 2026-04-29 M98 Axis 1 교정 이력 상세 조회

## 변경 파일

- `app/handlers/corrections.py`
- `app/web.py`
- `app/frontend/src/api/client.ts`
- `app/frontend/src/components/PreferencePanel.tsx`
- `e2e/tests/web-smoke.spec.mjs`
- `work/4/29/2026-04-29-m98-axis1-correction-history.md`

## 사용 skill

- `e2e-smoke-triage`: 교정 상세 패널의 selector와 Playwright 시나리오 추가 범위를 점검했다.
- `finalize-lite`: 구현 후 검증 사실, 미실행 항목, 문서 동기화 제외 사유를 정리했다.
- `work-log-closeout`: 변경 파일, 실행한 검증, 남은 리스크를 현재 `/work` 형식으로 기록했다.

## 변경 이유

- M98 Axis 1 handoff CONTROL_SEQ 1441에 따라 선호도 기반 교정 이력 항목에서 원문, 교정 결과, 교정 이유를 확인할 수 있는 상세 조회 흐름을 구현했다.
- 이전 handoff의 블록 원인이었던 `app/web.py` 라우팅 범위 누락이 이번 handoff에서 해소되어 `/api/corrections/<id>` GET 경로를 추가했다.

## 핵심 변경

- `CorrectionHandlerMixin.get_correction_detail(correction_id)`를 추가해 `correction_store.get()` 기반 상세 레코드를 반환하도록 했다.
- `LocalAssistantHandler.do_GET`에 `/api/corrections/<id>` 라우팅을 `/summary`, `/list` 고정 경로 뒤에 추가했다.
- 프런트엔드 API client에 `CorrectionDetailRecord`, `CorrectionDetailResponse`, `fetchCorrectionDetail()`을 추가했다.
- `PreferencePanel`의 최근 교정 항목을 클릭/Enter/Space로 선택할 수 있게 하고, `data-testid="correction-detail-panel"` 상세 패널에 원문, 교정 결과, delta summary 기반 교정 이유를 표시했다.
- `web-smoke.spec.mjs`에 교정 목록 항목 클릭 후 상세 패널이 열리고 원문/교정/이유가 표시되는 시나리오를 추가했다.

## 검증

- 통과: `git diff --name-status HEAD origin/feat/m96-bundle -- app/handlers/corrections.py app/web.py app/frontend/src/api/client.ts app/frontend/src/components/PreferencePanel.tsx e2e/tests/web-smoke.spec.mjs` → 변경 전 대상 파일 차이 없음
- 통과: `git merge-base --is-ancestor origin/feat/m97-axis1-bundle HEAD`
- 통과: `python3 -m py_compile app/handlers/corrections.py app/web.py`
- 미실행: `python3 -m unittest -v tests/test_corrections.py` → `tests/test_corrections.py` 파일 없음
- 통과: `python3 -m unittest -v tests/test_correction_summary.py` → 7 tests OK
- 통과: `cd app/frontend && npx tsc --noEmit`
- 통과: `git diff --check -- app/handlers/corrections.py app/web.py app/frontend/src/api/client.ts app/frontend/src/components/PreferencePanel.tsx e2e/tests/web-smoke.spec.mjs`
- 미실행: Playwright E2E 실제 실행은 handoff에서 로컬 실행 불필요 및 CI 위임으로 지정되어 수행하지 않았다.
- 실패(환경 제약): `git switch -c feat/m98-axis1-correction-history origin/feat/m96-bundle` → `.git/index.lock` 생성이 읽기 전용 파일시스템으로 차단됨. 대상 파일은 `origin/feat/m96-bundle`과 동일한 상태에서 작업했다.

## 남은 리스크

- 로컬 브랜치 생성은 `.git` 쓰기 제한으로 실패해 현재 브랜치명은 `feat/m97-axis1-bundle` 상태다. 다만 구현 전 대상 5개 파일은 `origin/feat/m96-bundle`과 차이가 없었고 M97 변경 포함 여부는 확인했다.
- 새 Playwright 시나리오는 추가했지만 로컬 브라우저 실행은 하지 않았으므로 CI에서 `correction list item click shows correction detail panel` 포함 smoke 확인이 필요하다.
- UI 동작 변경에 따른 제품 문서 동기화는 이번 implement handoff의 5개 파일 경계 밖이라 수행하지 않았다.
