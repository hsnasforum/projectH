# 2026-04-29 M86 번들 및 머지 게이트 정지 해결 제언 (Gemini)

## 1. 개요
M86 Doc Sync (`verify/1322`) 단계에서 발생한 'uncommitted dirty tree'와 '출처 불명 monitor.py 변경' 문제를 해결하고, 정체된 머지 게이트(`operator_request/1322`)를 해소하기 위한 권고입니다.

## 2. 조사 및 판단

### 2.1. monitor.py 변경 건 출처 확인
- `verify/1322`에서 "미상"으로 보고되었던 `controller/monitor.py` 및 관련 테스트 변경은 `work/4/29/2026-04-29-gemini-approval-marker-reset.md`를 통해 공식적인 구현 및 검증 사실이 확인되었습니다.
- 해당 작업은 Gemini의 stale approval marker를 초기화하는 유효한 버그 수정입니다.

### 2.2. 작업트리(Dirty Tree) 상태
- 현재 작업트리에 남은 uncommitted 파일들:
    - `storage/sqlite/preference.py`, `tests/test_sqlite_store.py` (M86 Axis 1)
    - `docs/MILESTONES.md`, `docs/TASK_BACKLOG.md` (M86 doc sync)
    - `controller/monitor.py`, `tests/test_controller_monitor.py` (Approval Reset fix)
- 위 모든 파일은 각각의 `/work` 및 `/verify`를 통해 구현 의도와 기술적 정당성이 확보된 상태입니다.

### 2.3. 결정 지점 (Decision Point)
- `operator_request/1322`에서 요구한 "C. monitor.py 미기록 변경 처리"에 대한 불확실성이 제거되었습니다.
- 모든 PR(#71-#75) 및 로컬 번들은 상호 충돌 없이 머지 및 커밋이 가능합니다.
- 단, 머지 실행과 대규모 번들 커밋/push는 `GEMINI.md` 및 `operator_policy`에 따라 오퍼레이터의 승인이 필요한 영역입니다.

## 3. 권고 (Recommendation)

**RECOMMEND: needs_operator authorize_m86_bundle_and_pr_merge**

### 상세 가이드:
1. **번들 커밋:** 현재 작업트리의 6개 파일(M86 Axis 1 + Doc Sync + Monitor Fix)을 `feat/m86-bundle-and-fixes` 성격의 단일 번들로 커밋 및 push 승인.
2. **PR 머지:** 기존 오픈된 PR #71~#75의 순차적 머지 실행 승인.
3. **통합:** 모든 머지 완료 후 main 브랜치 기준으로 M87 계획 수립 라운드로 전환.

---
**STATUS:** advice_ready
**CONTROL_SEQ:** 1328
