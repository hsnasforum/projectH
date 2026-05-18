STATUS: verified
CONTROL_SEQ: 1390
BASED_ON_WORK: work/4/29/2026-04-29-m96-axis1-pref-navigate-testid.md
VERIFIED_BY: Claude (verify owner)
NEXT_CONTROL: implement_handoff.md CONTROL_SEQ 1390

---

# 2026-04-29 M96 Axis 1 — 선호 카드 이동 링크 data-testid 추가 — verify

## 이번 라운드 범위

`MessageBubble.tsx` "선호에서 보기" anchor에 `data-testid="pref-navigate-to-card"` 추가.
팝오버 내 모든 인터랙티브 요소가 `data-testid` 패턴을 갖도록 불일치 해소.
TypeScript only — dist rebuild는 Axis 2 대상.

## 직접 실행 결과

| 체크 | 결과 |
|------|------|
| `cd app/frontend && npx tsc --noEmit` | **PASS** |
| `git diff --check -- MessageBubble.tsx` | **PASS** |
| `git status --short -- app/static/dist e2e` | **출력 없음** ✓ |

## 구현 클레임 확인

| 클레임 | 확인 결과 |
|--------|---------|
| `MessageBubble.tsx:621` `data-testid="pref-navigate-to-card"` 추가 | ✓ |
| `href`, class, onClick 동작 미변경 | ✓ |
| `fullPref?.preference_id` 조건 유지 | ✓ |
| dist·e2e 미변경 | ✓ |

## Dirty Tree (브랜치: feat/m95-bundle, HEAD 18a246e)

| 파일 | 출처 | 상태 |
|------|------|------|
| `app/frontend/src/components/MessageBubble.tsx` | M96 Axis 1 | M (uncommitted) |

## 남은 리스크

- M96 Axis 2 대상: dist 재빌드 + preference E2E 격리 실행.
- 브랜치 생성은 `.git/refs` 쓰기 제한으로 수행하지 못했다. uncommitted 상태.
