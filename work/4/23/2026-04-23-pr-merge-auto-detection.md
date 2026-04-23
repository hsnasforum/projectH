# 2026-04-23 PR merge auto-detection (PrMergeStatusCache)

## 변경 파일
- `pipeline_runtime/pr_merge_state.py` (신규)
- `pipeline_runtime/operator_autonomy.py`
- `pipeline_runtime/supervisor.py`
- `watcher_core.py`
- `tests/test_pr_merge_state.py` (신규)
- `tests/test_operator_request_schema.py`
- `tests/test_pipeline_runtime_supervisor.py`
- `tests/test_watcher_core.py`
- `README.md`
- `.pipeline/README.md`
- `docs/projectH_pipeline_runtime_docs/03_기술설계_명세서.md`
- `docs/projectH_pipeline_runtime_docs/05_운영_RUNBOOK.md`
- `report/gemini/2026-04-23-pr-merge-auto-detection-safety-review.md`

## 구현 배경

pr-merge-gate-loop-guard(seq 1) 이후, `pr_merge_gate` operator stop이 PR merge 이후에도 stale `needs_operator`로 남는 문제가 있었습니다. operator가 GitHub에서 PR을 직접 merge하면 그 사실을 pipeline이 감지해 stop을 자동 해소하는 것이 자연스러운 완결입니다. Gemini advisory(CONTROL_SEQ 4)는 이를 "operator 행위의 자동 인식으로 승인 모델 범위 내"로 확인했습니다.

## 핵심 변경

### `pipeline_runtime/pr_merge_state.py` (신규)

- `PrMergeStatusCache`: `gh pr view <N> --json state,mergedAt,headRefOid`로 PR merged 여부를 조회하는 TTL 캐시
  - success_ttl=5min, miss_ttl=15sec, timeout=4sec
  - `shutil.which("gh") is None` guard → fail-closed `_PR_MERGE_PENDING`
  - OSError / TimeoutExpired / JSONDecodeError → fail-closed
  - HEAD SHA 검증: control text에 `HEAD: <sha>` 선언이 있으면 GitHub `headRefOid`와 prefix match — 불일치 시 `head_mismatch` (완료로 취급하지 않음)
- `PrMergeGateResolution` dataclass: `completed_pr_numbers` + `head_mismatch_pr_numbers`
- `_expected_head_sha()` / `_sha_matches()`: control text / meta에서 HEAD SHA 파싱 + prefix 매칭

### `pipeline_runtime/operator_autonomy.py`

- `_PR_NUMBER_RE` / `referenced_operator_pr_numbers()`: control text에서 PR 번호 파싱
- `evaluate_stale_operator_control()` — `completed_pr_numbers` 파라미터 추가: `pr_merge_gate` reason이고 참조 PR이 completed_prs에 있으면 `{"reason": "pr_merge_completed"}` 반환

### `pipeline_runtime/supervisor.py`, `watcher_core.py`

- `PrMergeStatusCache` 인스턴스 통합: `_pr_merge_status_cache`
- `_check_stale_operator_control()`에서 `completed_pr_numbers` 전달

### 문서 3종

- `.pipeline/README.md`: `pr_merge_gate` 자동 해소 조건 및 fail-closed 계약 추가
- `README.md`: 동일 내용 반영
- `03_기술설계_명세서.md` / `05_운영_RUNBOOK.md`: `pr_merge_completed` recovery 경로 및 운영 체크 포인트 추가

## 검증

- `python3 -m py_compile pipeline_runtime/operator_autonomy.py pipeline_runtime/supervisor.py pipeline_runtime/pr_merge_state.py watcher_core.py tests/test_pr_merge_state.py` → OK
- `python3 -m unittest tests.test_pr_merge_state -v` → 2/2 OK
- `python3 -m unittest tests.test_operator_request_schema tests.test_pipeline_runtime_supervisor tests.test_turn_arbitration tests.test_watcher_core -v` → 362/362 OK
- Advisory CONTROL_SEQ 4: "Option A 승인 — 소급 work note + commit 진행"

## 남은 리스크

- `supervisor.py` / `watcher_core.py`는 `completed_pr_numbers()`만 사용 — `control_resolution()` (head_mismatch 분기)은 미통합. 현재 사용 패턴에서는 mismatch가 조용히 무시됨. 별도 라운드 미결.
- PR #27 merge: operator 결정 (CONTROL_SEQ 5 operator_request에서 처리)
- Axis 5b (PreferencePanel.tsx): PR merge 후 별도 라운드
