STATUS: verified
CONTROL_SEQ: 1469
BASED_ON_WORK: work/4/30/2026-04-30-m105-correction-history-status-filter.md
VERIFIED_BY: Claude (verify owner)
NEXT_CONTROL: implement_handoff.md CONTROL_SEQ 1469

---

# 2026-04-30 M105 Axis 1 correction history status filter — verify

## 이번 라운드 범위

CONTROL_SEQ 1468 implement_handoff (m105_axis1_correction_history_status_filter) 실행 결과.
work note 변경 범위: 2개 파일 (TypeScript 1개 + test 1개).
`app/frontend/src/api/client.ts` 수정 없음 — 기존 `fetchCorrectionList({ status })`가 이미 status 지원.
테스트 위치: handoff 지시의 `test_web_app.py` 대신 `tests/test_correction_summary.py` — 더 적합한 위치.

## 직접 실행 결과

| 체크 | 결과 |
|------|------|
| `tsc --noEmit -p app/frontend/tsconfig.json` | **PASS** |
| `test_correction_list_filters_by_status` | **PASS** (1 test, 0.003s) |
| `git diff --check` (2개 파일) | **PASS** |
| `data-testid="correction-status-filter"` 존재 | ✓ `PreferencePanel.tsx:590` |

## M105 Axis 1 핵심 변경 요약

- `PreferencePanel.tsx`: `CorrectionStatusFilter` + `correction-status-filter` select 드롭다운; 상태 변경 시 `fetchCorrectionList({ status })` 재호출; "전체" 선택 시 status 파라미터 생략; 기존 상세 선택 초기화
- `tests/test_correction_summary.py`: `test_correction_list_filters_by_status` — status="confirmed" 필터가 해당 교정만 반환하는지 검증

## 남은 리스크

- dist 재빌드 미실행 — Axis 2에서 처리
- E2E 시나리오 미추가 — Axis 2 범위
- docs 동기화 미실행 — 3+ rule로 publish commit에 번들 예정
- 2개 파일 모두 미커밋 상태
