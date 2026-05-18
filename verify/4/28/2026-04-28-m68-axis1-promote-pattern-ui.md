STATUS: verified
CONTROL_SEQ: 1238
BASED_ON_HANDOFF: .pipeline/implement_handoff.md CONTROL_SEQ 1237
BASED_ON_WORK: work/4/28/2026-04-28-m68-axis1-promote-pattern-ui.md
VERIFIED_BY: Claude (verify owner)
NEXT_CONTROL: implement_handoff.md CONTROL_SEQ 1238

---

# 2026-04-28 M68 Axis 1 — promote-pattern backend + UI 검증

## 이번 라운드 범위

- `storage/correction_store.py` — `promote_by_fingerprint()` 추가
- `storage/sqlite_store.py` — `promote_by_fingerprint()` 추가 (SQLite parity)
- `app/handlers/aggregate.py` — `promote_correction_pattern()` 서비스 메서드 추가
- `app/web.py` — `POST /api/corrections/promote-pattern` 라우팅 추가
- `app/frontend/src/api/client.ts` — `promoteCorrectionPattern()` client 함수 추가
- `app/frontend/src/components/PreferencePanel.tsx` — `승격` 버튼 추가 (data-testid="correction-promote-pattern")
- `tests/test_correction_store.py` — CONFIRMED-only promotion + skip + empty 케이스 추가
- `tests/test_sqlite_store.py` — 동일 3케이스 SQLite 대상

## 직접 실행 결과

| 체크 | 결과 |
|------|------|
| 심볼 존재 확인 (`promote_by_fingerprint`, `promote_correction_pattern`, `promoteCorrectionPattern`, `correction-promote-pattern`) | **PASS** (6개 파일에서 모두 확인) |
| `python3 -m py_compile` (4개 백엔드 파일) | **PASS** |
| `python3 -m unittest -v tests.test_correction_store` | **PASS — 31 tests** |
| `python3 -m unittest -v tests.test_sqlite_store` | **PASS — 35 tests** |
| `tsc --noEmit` | **PASS (exit 0)** |
| `git diff --check` (8개 파일) | **PASS** |

## 구현 클레임 확인

| 클레임 | 위치 | 확인 결과 |
|--------|------|---------|
| `promote_by_fingerprint` JSON | `correction_store.py:156` | ✓ CONFIRMED-only 필터 확인 |
| `promote_by_fingerprint` SQLite | `sqlite_store.py:926` | ✓ 동일 패턴 |
| `promote_correction_pattern` + `record_reviewed_candidate_preference` 호출 | `aggregate.py:88–115` | ✓ source_refs 포함 |
| POST 라우팅 | `web.py:408, 430` | ✓ allowlist + dispatch |
| `promoteCorrectionPattern` client | `client.ts:379` | ✓ |
| `승격` 버튼 | `PreferencePanel.tsx:343` (data-testid="correction-promote-pattern") | ✓ |
| commit / push 미실행 | git log 확인 (HEAD: 8ab591f) | ✓ |

## 브랜치 / 커밋 상태

- 현재 브랜치: `feat/m50-axis1-axis2-pref-visibility` (HEAD: 8ab591f)
- 브랜치 전환 실패(`git/index.lock`): implement 환경 제약. M68 Axis 1 변경은 working tree에만 존재
- 8개 파일 미커밋 상태 — 예상된 상태 (handoff가 commit 금지)

## M68 완성 상태

| Axis | 내용 | 상태 |
|------|------|------|
| 1 | backend + frontend code (promote-pattern) | ✓ 이번 라운드 |
| 2 | dist 재빌드 + E2E 격리 | → 다음 슬라이스 |

## 다음 행동

M68 Axis 2: `app/static/dist/` 재빌드 + E2E 격리 시나리오 + MILESTONES.md.
→ `implement_handoff.md` CONTROL_SEQ 1238.
