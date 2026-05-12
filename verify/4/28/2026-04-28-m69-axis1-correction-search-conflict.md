STATUS: verified
CONTROL_SEQ: 1244
BASED_ON_HANDOFF: .pipeline/implement_handoff.md CONTROL_SEQ 1243
BASED_ON_WORK: work/4/28/2026-04-28-m69-axis1-correction-search-conflict.md
VERIFIED_BY: Claude (verify owner)
NEXT_CONTROL: implement_handoff.md CONTROL_SEQ 1244

---

# 2026-04-28 M69 Axis 1 — 교정 목록 검색/필터 + 충돌 신호 검증

## 이번 라운드 범위

- `storage/correction_store.py` — `list_filtered(query, status, limit)` 추가
- `storage/sqlite_store.py` — `list_filtered()` SQLite parity (json_extract 기반)
- `app/handlers/aggregate.py` — `get_correction_list(query, status)` + `has_active_preference` 충돌 신호
- `app/web.py` — `/api/corrections/list?query=&status=` GET 파라미터 파싱
- `app/frontend/src/api/client.ts` — `fetchCorrectionList(params?)` + `has_active_preference?` 타입
- `app/frontend/src/components/PreferencePanel.tsx` — 검색 input + `[충돌]` 배지
- `tests/test_correction_store.py` — 4케이스 추가 (query/status/AND/empty)
- `tests/test_sqlite_store.py` — 4케이스 추가 (동일)

## 직접 실행 결과

| 체크 | 결과 |
|------|------|
| 심볼 존재 확인 (`list_filtered` ×2, `has_active_preference`, `correction-search-input`, `correction-conflict-badge`) | **PASS** |
| `python3 -m py_compile` (백엔드 4개 파일) | **PASS** |
| `tsc --noEmit` | **PASS (exit 0)** |
| `python3 -m unittest tests.test_correction_store` | **PASS — 35 tests** |
| `python3 -m unittest tests.test_sqlite_store` | **PASS — 39 tests** |
| `git diff --check` (8개 파일) | **PASS** |

## 구현 클레임 확인

| 클레임 | 위치 | 확인 결과 |
|--------|------|---------|
| `CorrectionStore.list_filtered()` | `correction_store.py:215` | ✓ query/status AND 필터 + 최신순 |
| `SQLiteCorrectionStore.list_filtered()` | `sqlite_store.py:789` | ✓ `json_extract(data, '$.original_text')` LIKE 패턴 |
| `get_correction_list(query, status)` + 충돌 신호 | `aggregate.py:70–96` | ✓ `has_active_preference` 붙임 |
| `/api/corrections/list?query=&status=` | `web.py:357–362` | ✓ `parse_qs` 파싱 |
| `fetchCorrectionList(params?)` | `client.ts:354` | ✓ URL params 추가 |
| 검색 input | `PreferencePanel.tsx:362` (data-testid="correction-search-input") | ✓ |
| 충돌 배지 | `PreferencePanel.tsx:377, 379` (data-testid="correction-conflict-badge") | ✓ |
| commit / push 미실행 | HEAD: 9b5943f (M68 Axis 2) | ✓ |

## 구현 노트

- `get_correction_list`가 `getattr(self, "preference_store", None)` 방어 패턴 사용 — 의도적 안전 가드, 동작 동일
- SQLite는 컬럼 `original_text`/`corrected_text` 없이 `data` JSON 컬럼에서 `json_extract` 사용 — 올바른 어댑테이션
- 브랜치 전환 실패 (`feat/m68-promote-pattern` 유지) — 예상된 환경 제약, uncommitted 상태 정상

## M69 완성 상태

| Axis | 내용 | 상태 |
|------|------|------|
| 1 | backend + frontend code (검색/필터 + 충돌 신호) | ✓ 이번 라운드 |
| 2 | dist 재빌드 + E2E 격리 | → 다음 슬라이스 |

## 다음 행동

M69 Axis 2: `app/static/dist/` 재빌드 + E2E 격리 시나리오 + MILESTONES.md.
→ `implement_handoff.md` CONTROL_SEQ 1244.
