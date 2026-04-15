# 검토 후보 action vocabulary 확장: reject, defer

## 변경 파일

- `core/contracts.py`
- `app/handlers/aggregate.py`
- `app/serializers.py`
- `app/templates/index.html`
- `app/static/app.js`
- `tests/test_web_app.py`
- `tests/test_contracts.py`
- `e2e/tests/web-smoke.spec.mjs`
- `README.md`
- `docs/PRODUCT_SPEC.md`
- `docs/ACCEPTANCE_CRITERIA.md`

## 사용 skill

- 없음

## 변경 이유

reviewed-memory lifecycle parity family가 이미 닫혀 있고, 현재 shipped shell의 `검토 후보` 표면이 accept-only로 보이는 가시적 한계를 줄이는 슬라이스입니다. `reject`와 `defer`는 기존 `candidate_review_record` 경로를 재사용하며, memory apply나 user-level memory write, 편집 UI를 열지 않습니다.

## 핵심 변경

1. **`core/contracts.py`**: `CandidateReviewAction`에 `REJECT`, `DEFER` 추가. `CANDIDATE_REVIEW_ACTION_TO_STATUS` 맵에 `reject → rejected`, `defer → deferred` 추가.
2. **`app/handlers/aggregate.py`**: accept-only 하드코딩을 `CANDIDATE_REVIEW_ACTION_TO_STATUS` 기반 동적 검증으로 교체. 에러 메시지를 action-neutral 한국어로 수정. `review_action`/`review_status`를 맵에서 읽어 record에 기록.
3. **`app/serializers.py`**: `_serialize_candidate_review_record`의 accept-only 검증을 `CANDIDATE_REVIEW_ACTION_TO_STATUS` 기반으로 교체. reject/defer record도 정상 직렬화됨.
4. **`app/templates/index.html`** + **`app/static/app.js`**: hint 텍스트를 "후보를 수락, 거절, 또는 보류할 수 있습니다. 아직 적용이나 편집은 열지 않았습니다."로 교체. `submitCandidateReviewAccept` → `submitCandidateReview(item, reviewAction)` 범용화. 버튼 3개: `검토 수락`/`거절`/`보류` (각각 `data-testid` review-queue-accept/reject/defer).
5. **`storage/session_store.py`**: 변경 없음 — 기존 `_normalize_candidate_review_record`가 `ALLOWED_CANDIDATE_REVIEW_ACTION_TO_STATUS`를 사용하므로 contracts 맵 확장만으로 자동 수용.

## 검증

- `python3 -m pytest tests/test_contracts.py -x -q` → 45 passed
- `python3 -m pytest tests/test_web_app.py -x -q -k "test_submit_candidate_review_reject or test_submit_candidate_review_defer or test_submit_candidate_review_rejects_invalid or test_submit_candidate_review_accept_records"` → 4 passed
- `python3 -m pytest tests/test_web_app.py -x -q` → 266 passed
- `cd e2e && npx playwright test tests/web-smoke.spec.mjs -g "candidate confirmation path는 save support와 분리되어 기록되고 later correction으로 current state에서 사라집니다" --reporter=line` → 1 passed
- `cd e2e && npx playwright test tests/web-smoke.spec.mjs -g "same-session recurrence aggregate" --reporter=line` → 1 passed
- `git diff --check` → clean

## 남은 리스크

- reject/defer는 reviewed-but-not-applied 결과만 남기며, 이 결과를 근거로 aggregate apply나 memory effect가 바뀌는 로직은 아직 없습니다. 향후 reject 된 candidate에 대한 aggregate 제외 논리가 필요할 수 있습니다.
- `make e2e-test` full suite는 실행하지 않았습니다. 변경이 기존 review-queue 경로 내부에 한정되어 있고, 두 개의 focused 시나리오가 통과했으므로 broad drift 위험은 낮습니다.
