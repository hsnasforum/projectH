STATUS: verified
CONTROL_SEQ: 1296
BASED_ON_HANDOFF: .pipeline/implement_handoff.md CONTROL_SEQ 1295
BASED_ON_WORK: work/4/29/2026-04-29-m82-promote-activated-count.md
VERIFIED_BY: Claude (verify owner)
NEXT_CONTROL: operator_request.md CONTROL_SEQ 1296

---

# 2026-04-29 M82 Axis 1 — promote-pattern 응답 activated_count 추가

## 이번 라운드 범위

- `app/handlers/corrections.py` — `activated_count` 추적 + 응답 추가
- `app/frontend/src/api/client.ts` — `promoteCorrectionPattern` 반환 타입 `activated_count?: number` 추가

## 직접 실행 결과

| 체크 | 결과 |
|------|------|
| `python3 -m py_compile app/handlers/corrections.py` | **PASS** |
| `tsc --noEmit` | **PASS (exit 0)** |
| `python3 -m unittest tests.test_smoke` | **PASS — 150 tests** |
| `git diff --check` (2개 파일) | **PASS** |

## 구현 확인

| 항목 | 위치 | 확인 결과 |
|------|------|---------|
| `activated_count = 0` 초기화 | `corrections.py:109` | ✓ |
| `result is not None` 조건 카운트 | `corrections.py:133` | ✓ |
| 응답에 `"activated_count"` 포함 | `corrections.py:137` | ✓ |
| client.ts 반환 타입 (Promise 선언) | `client.ts:388` | ✓ `activated_count?: number` |
| client.ts 반환 타입 (res.json cast) | `client.ts:395` | ✓ `activated_count?: number` |
| commit / push 미실행 | HEAD: abe52b2 | ✓ |

## 다음 행동

M82 완료. 2개 파일 커밋 + 스택 브랜치 push + PR 생성.
→ `operator_request.md` CONTROL_SEQ 1296.
