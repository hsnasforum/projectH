# 2026-04-22 Milestone 7 Axis 2: CandidateReviewAction EDIT (partial)

## 변경 파일
- `core/contracts.py`
- `app/handlers/aggregate.py`
- `app/static/app.js`

(storage gap으로 인해 CONTROL_SEQ 807 범위 내 3파일만 적용. `storage/session_store.py` 변경은 CONTROL_SEQ 808로 위임.)

## 사용 skill
- `finalize-lite`: 구현 마무리 검증 및 closeout 준비에 사용

## 변경 이유
- Milestone 7 Axis 2: 리뷰 큐에 "검토됐지만 적용 안 됨" 의미를 가진 `CandidateReviewAction.EDIT` 추가
- 기존 ACCEPT/REJECT/DEFER에 편집 의견 기록 경로 신설

## 핵심 변경

### `core/contracts.py`
- `CandidateReviewAction.EDIT = "edit"` 추가
- `CANDIDATE_REVIEW_ACTION_TO_STATUS["edit"] = "edited"` 추가
- `ALLOWED_CANDIDATE_REVIEW_ACTION_TO_STATUS`는 contracts.py dict의 alias이므로 자동 포함

### `app/handlers/aggregate.py`
- `submit_candidate_review`에서 `reason_note = self._normalize_optional_text(payload.get("reason_note"))` 추출
- `candidate_review_record` dict에 `**({"reason_note": reason_note} if reason_note else {})` 추가

### `app/static/app.js`
- `formatReviewOutcomeLabel`: `"edit"` → `"검토 편집됨"` 분기 추가
- `REVIEW_ACTION_NOTICES`: `edit: "검토 후보에 편집 의견을 기록했습니다."` 추가
- `submitCandidateReview(item, reviewAction, reasonNote)`: 선택적 세 번째 파라미터 추가 + fetch body에 `reason_note` 포함
- 리뷰 큐 편집 버튼: `deferButton` 다음에 인라인 textarea + 확인 버튼 포함 편집 영역 추가

## 검증
- `python3 -m py_compile core/contracts.py app/handlers/aggregate.py` → OK
- `python3 -m unittest tests.test_smoke -q` → 150 tests OK
- `git diff --check -- core/contracts.py app/handlers/aggregate.py app/static/app.js` → OK

## 남은 리스크

### 스토리지 gap (CONTROL_SEQ 808 대상)
- `storage/session_store.py:_normalize_candidate_review_record`(line 280-319) return dict에 `reason_note`가 없어 aggregate.py에서 전달한 `reason_note`가 storage 단에서 silently drop됨
- CONTROL_SEQ 807 handoff의 "`_normalize_candidate_review_record`(line ~232) already handles `reason_note`" 주장은 오류: 해당 line 232는 실제로 `_normalize_content_reason_record` 안의 코드였음
- 편집 버튼 UI 동작은 가능하나 편집 의견이 저장되지 않는 상태 — CONTROL_SEQ 808 스토리지 수정 후 완전 기능

### 기타
- 편집 버튼 다중 클릭 시 editArea div 중복 append 가능성 (UX minor)
- Playwright browser smoke 미실행 (편집 버튼 기능 정확성 미확인)
- doc sync (README, PRODUCT_SPEC, ACCEPTANCE_CRITERIA) verify 라운드로 위임
- Axis 1 + Axis 2 bundle commit/push는 advisory seq 806 지시에 따라 storage fix 완료 후 verify/handoff 라운드에서 처리
