# 2026-03-31 claim coverage status tag clarity

## 변경 파일
- `app/templates/index.html`
- `docs/ACCEPTANCE_CRITERIA.md`

## 사용 skill
- 없음

## 변경 이유
- TASK_BACKLOG "Current Phase In Progress" 항목 4: "Distinguish strong facts, single-source facts, and unresolved slots more clearly"
- MILESTONES "Milestone 4: Secondary-Mode Investigation Hardening" — source role labeling, stronger weighting, better separation
- claim-coverage 패널에서 `교차 확인`, `단일 출처`, `미확인` 상태가 슬롯 이름 뒤에 섞여 있어 빠른 스캔이 어려웠음

## 핵심 변경

### UI 변경 (claim coverage panel)
**이전 형식:**
```
1. 출생일 · 교차 확인
   값: 1990년 3월 15일
   근거 2건
```

**개선 형식:**
```
1. [교차 확인] 출생일
   값: 1990년 3월 15일
   근거 2건
2. [단일 출처] 소속
   값: A 대학교
   → 1개 출처만 확인됨. 교차 검증이 권장됩니다.
3. [미확인] 수상 이력
   → 추가 출처가 필요합니다.
```

변경 내용:
- 상태 태그(`[교차 확인]`, `[단일 출처]`, `[미확인]`)를 각 행 앞쪽으로 이동
- `미확인` 슬롯에 "추가 출처가 필요합니다" 행동 힌트 추가
- `단일 출처` 슬롯에 "1개 출처만 확인됨. 교차 검증이 권장됩니다" 행동 힌트 추가
- `교차 확인`(strong) 슬롯은 추가 힌트 없이 값만 표시

### docs 반영
- `docs/ACCEPTANCE_CRITERIA.md`: claim coverage 항목에 status tag leading + actionable hints 명시

### 변경하지 않은 것
- backend claim-coverage 로직 변경 없음
- search ranking, source weighting, probe query 변경 없음
- 패널 hint 텍스트("교차 확인은 여러 출처 합의...") 변경 없음

## 검증
- `make e2e-test` — `12 passed (2.5m)`
- `git diff --check` — 통과

## 남은 리스크
- claim coverage는 web investigation에서만 생성되므로 mock adapter 테스트에서는 이 surface를 직접 검증하는 dedicated smoke가 없음 (claim-coverage 데이터가 mock 응답에 포함되지 않음)
- dirty worktree는 여전히 넓음 (이번 라운드에서 unrelated 변경을 건드리지 않음)
