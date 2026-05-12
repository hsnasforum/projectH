# 2026-04-28 Control Recovery → M68 Axis 1 Handoff

## 목표

PR merge 완료 후 스테일 control(CONTROL_SEQ 1234)을 제거하고 런타임이 idle 상태에 머물지
않도록 정확히 하나의 next control(CONTROL_SEQ 1235)을 작성한다.

## 이번 라운드 직접 편집 파일

| 파일 | 변경 내용 |
|------|---------|
| `.pipeline/implement_handoff.md` | CONTROL_SEQ 1235, M68 Axis 1 promote-pattern 핸드오프 |
| `watcher_core.py` | pr_merge_completed recovery follow-up no-next-control 감지 추가 (commit 8ab591f) |
| `tests/test_watcher_core.py` | replay test 추가 (commit 8ab591f) |
| `docs/projectH_pipeline_runtime_docs/03_기술설계_명세서.md` | doc-sync: recovery follow-up → advisory 승격 계약 (commit 8ab591f) |
| `docs/projectH_pipeline_runtime_docs/05_운영_RUNBOOK.md` | doc-sync: 동일 (commit 8ab591f) |

## Council 결정

```
COUNCIL_DECISION: implement
REASON_CODE: m68_axis1_direction_confirmed_by_existing_advisory
NEXT_CONTROL_FILE: .pipeline/implement_handoff.md
NEXT_CONTROL_SEQ: 1235
EVIDENCE:
- report/gemini/2026-04-28-m67-completion-and-m68-direction.md
  → RECOMMEND: implement M68 Axis 1 — Pattern-level promotion to Preference
- verify/4/28/2026-04-28-m67-axis2-correction-list-dist-e2e.md: STATUS verified
REJECTED:
- advisory_request: M68 방향 이미 기존 advisory로 확정됨
- operator_request: 실제 operator 경계(파괴적 작업/auth/approval-record) 없음
```

## 검증

- `python3 -m py_compile watcher_core.py` → PASS (commit 전)
- `python3 -m unittest -v tests.test_watcher_core` (207 tests) → PASS (commit 전)
- `git status` 확인: watcher 4개 파일 클린 (commit 8ab591f 완료)

## 남은 사항

- watcher 변경(commit 8ab591f)의 push/PR 생성 → operator boundary; 별도 처리
- M68 Axis 1 implement 실행 → Codex 담당
- M68 Axis 2 (dist 재빌드 + E2E + 승격 버튼 UI) → M68 Axis 1 완료 후

## 다음 제어 슬롯

`.pipeline/implement_handoff.md` CONTROL_SEQ 1235 — M68 Axis 1 promote-pattern
