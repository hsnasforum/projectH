STATUS: verified
CONTROL_SEQ: 258
BASED_ON_WORK: work/4/26/2026-04-26-m42-doc-sync-architecture.md
BASED_ON_HANDOFF: .pipeline/implement_handoff.md CONTROL_SEQ 257
VERIFIED_BY: Claude
NEXT_CONTROL: implement_handoff.md CONTROL_SEQ 258

---

# 2026-04-26 M42 doc-sync ARCHITECTURE.md 검증

## 이번 라운드 범위

docs-only 변경 2개 파일 검증: `docs/ARCHITECTURE.md`, `docs/MILESTONES.md`
코드·테스트 변경 없음.

## 직접 실행 결과

| 체크 | 결과 |
|------|------|
| `git diff --check -- docs/ARCHITECTURE.md docs/MILESTONES.md` | **PASS** (trailing whitespace 없음) |
| `python3 -m py_compile app/handlers/preferences.py` | 코드 미변경 확인 → 별도 실행 불필요 (이전 verify 255 PASS 유효) |

## Diff 리뷰

**`docs/ARCHITECTURE.md`** (단 1줄 확장):
- 원문 `list_preferences_payload()` 단락을 보존하고 끝에 두 문장 추가:
  - `active_count`, `candidate_count`, `paused_count` integer count 계약 명시 ✓
  - PreferencePanel status filter 탭 4개(전체/후보/활성/일시중지) + per-tab count 계약 명시 ✓
  - rejected 항상 숨김 계약 명시 ✓
- 원문 단락 변경 없음 ✓

**`docs/MILESTONES.md`** "Next 3 Implementation Priorities":
- 완료된 항목 1 (M42 A1) 및 항목 2 (watcher_core re-export 85c5210) 제거 ✓
- E2E 환경 개선 검증 → 항목 1로 승격 ✓
- M43 방향 확정 → 항목 2로 추가 ✓
- 항목 3 (ARCHITECTURE.md M42 doc-sync, "이번 라운드 구현 예정") 제거
  - 이유: 이번 라운드 완료됐으므로 "Next 3"에 잔류시키면 즉시 stale이 됨
  - 같은 날 5+ docs-only 라운드 누적(3+ 동일 family 규칙)에 따라 별도 라운드 없이 이 번들에서 직접 수정

## Dirty Tree 상태

| 파일 | 내용 | 커밋 여부 |
|------|------|-----------|
| `docs/ARCHITECTURE.md` | list_preferences_payload 단락 확장 | 미커밋 |
| `docs/MILESTONES.md` | Next 3 triage + item 3 stale 제거 | 미커밋 |

work note: `work/4/26/2026-04-26-m42-doc-sync-architecture.md` (untracked)
verify note: 이 파일 (untracked)

## 남은 리스크

- 두 파일 미커밋: commit_push_bundle_authorization을 verify/handoff lane에서 처리 필요
- unit 전체·Playwright: docs-only 라운드이므로 실행 불필요 (코드 미변경)
- "Next 3" 이제 2개 항목만 있음 (E2E 검증, M43 방향) — 세 번째는 advisory에서 확정 후 추가 가능
