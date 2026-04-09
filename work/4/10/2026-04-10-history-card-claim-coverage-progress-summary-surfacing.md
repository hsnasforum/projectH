# app.web history-card claim-coverage progress summary surfacing

## 변경 파일
- `storage/web_search_store.py`
- `app/serializers.py`
- `app/static/app.js`
- `tests/test_web_app.py`
- `e2e/tests/web-smoke.spec.mjs`
- `README.md`
- `docs/PRODUCT_SPEC.md`
- `docs/ACCEPTANCE_CRITERIA.md`
- `docs/MILESTONES.md`
- `docs/TASK_BACKLOG.md`

## 사용 skill
- 없음

## 변경 이유
- 저장된 웹 조사 기록에 `claim_coverage_progress_summary`가 이미 존재하지만, history card에서는 해당 텍스트가 누락되어 사용자가 기록을 다시 열지 않으면 재조사 진행 상태를 확인할 수 없었습니다.
- Milestone 4 investigation quality의 user-visible gap을 한 bounded slice로 닫습니다.

## 핵심 변경
1. **`storage/web_search_store.py`**: `list_session_record_summaries`에 `claim_coverage_progress_summary` 필드를 추가하여 store → serializer 경로에 진행 요약 텍스트를 전달합니다.
2. **`app/serializers.py`**: `_serialize_web_search_history`에서 `claim_coverage_progress_summary`를 `localize_text` 처리 후 payload에 포함합니다.
3. **`app/static/app.js`**: history card meta 영역에서 `claim_coverage_progress_summary`가 비어있지 않을 때 count summary 뒤에 진행 요약 텍스트를 추가합니다.
4. **`tests/test_web_app.py`**: store-level 및 serializer-level focused regression 2건 추가.
5. **`e2e/tests/web-smoke.spec.mjs`**: 기존 entity-card history-card test에 `claim_coverage_progress_summary` 전달 및 history card에서 progress summary가 보이는지 assertion 추가.
6. **docs**: `README.md`, `PRODUCT_SPEC.md`, `ACCEPTANCE_CRITERIA.md`, `MILESTONES.md`, `TASK_BACKLOG.md`에 history card progress summary 표시를 반영.

## 검증
- `python3 -m unittest tests.test_web_app` — 228 tests OK
- `cd e2e && npx playwright test tests/web-smoke.spec.mjs -g "history-card entity-card"` — 13 tests passed
- `git diff --check` — 공백 오류 없음

## 남은 리스크
- latest-update 카드나 비어있는 progress summary를 가진 카드에는 의도대로 진행 요약이 표시되지 않습니다. 이는 설계 의도입니다.
- 현재 e2e assertion은 첫 번째 entity-card test에만 추가되었습니다. 다른 entity-card test에 `claim_coverage_progress_summary`를 전달하는 것은 후속 smoke tightening에서 가능합니다.
