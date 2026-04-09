# history-card claim-coverage progress summary surfacing closeout

## 변경 파일
- `app/serializers.py` — `web_search_history` 직렬화에 `claim_coverage_progress_summary` 필드 추가
- `app/static/app.js` — history-card meta에 `claim_coverage_progress_summary` 텍스트 표시
- `tests/test_web_app.py` — `claim_coverage_progress_summary` store/serializer 회귀 테스트 2건 추가
- `e2e/tests/web-smoke.spec.mjs` — history-card entity-card 시나리오에 progress summary 텍스트 검증 추가
- `README.md` — investigation progress summary in history cards 문구 반영 (feature list + Playwright scenario list)
- `docs/PRODUCT_SPEC.md` — `web_search_history` payload에 `claim_coverage_progress_summary` 필드 문서화, history panel 설명에 progress summary 반영, Investigation 섹션 Implemented 항목 반영
- `docs/ACCEPTANCE_CRITERIA.md` — history card header badges 기준에 investigation progress summary 항목 추가
- `docs/MILESTONES.md` — Milestone 4 In Progress에 history-card progress summary surfacing shipped 표기
- `docs/TASK_BACKLOG.md` — shipped task list에 investigation progress summary 항목 반영

## 사용 skill
- 없음

## 변경 이유
- `claim_coverage_progress_summary`는 이미 claim-coverage panel과 response detail에서 생성·저장되고 있었으나, history-card에는 표시되지 않았음
- 이 슬라이스는 기존 저장 필드를 history-card payload와 browser rendering까지 surfacing하여 사용자가 이전 조사 기록을 다시 볼 때 progress 상태를 한눈에 파악할 수 있게 함
- seq13 핸드오프 이후 dirty tree에 이미 구현·테스트·docs가 들어와 있었으나 `/work` closeout이 없어 canonical truth가 닫히지 않은 상태였음

## 핵심 변경
1. **직렬화** (`app/serializers.py:285–287`): `web_search_history` 항목에 `claim_coverage_progress_summary`를 `localize_text` 후 포함
2. **브라우저 렌더링** (`app/static/app.js:2962–2965`): history-card meta 영역에 progress summary 텍스트가 비어 있지 않을 때 `detailLines`에 추가
3. **단위 테스트** (`tests/test_web_app.py:9649–9694, 9696–9731`):
   - `test_web_search_store_list_summaries_includes_claim_coverage_progress_summary`: store save → list_session_record_summaries에서 값 존재/부재 검증
   - `test_web_search_history_serializer_includes_claim_coverage_progress_summary`: service-level 직렬화 경로에서 값 전달 검증
4. **E2E** (`e2e/tests/web-smoke.spec.mjs:1264, 1275`): history-card entity-card 시나리오에 `claim_coverage_progress_summary` fixture 추가, `toContainText` 검증
5. **docs 정합**: README, PRODUCT_SPEC, ACCEPTANCE_CRITERIA, MILESTONES, TASK_BACKLOG에 일관된 progress summary 기술

## 검증
- `python3 -m unittest -v tests.test_web_app` → Ran 228 tests … OK
- `cd e2e && npx playwright test tests/web-smoke.spec.mjs -g "history-card entity-card" --reporter=line` → 13 passed
- `git diff --check` → 출력 없음 (공백 오류 없음)

## 남은 리스크
- history-card latest-update 카드에도 동일한 progress summary surfacing이 필요할 수 있으나, 현재 latest-update 시나리오에서는 해당 필드가 비어 있는 경우가 대부분이므로 현재 shipped contract 범위 안에서는 추가 작업 불필요
- `claim_coverage_progress_summary`의 빈 문자열 / null 경계 처리는 `localize_text(...).strip()` + JS `(... || "").trim()` 이중 방어로 현재 안전
