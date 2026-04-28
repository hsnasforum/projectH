STATUS: verified
CONTROL_SEQ: 1170
BASED_ON_WORK: work/4/28/2026-04-28-m50-axis3b-preference-not-applied-button.md
BASED_ON_HANDOFF: .pipeline/implement_handoff.md CONTROL_SEQ 1170
VERIFIED_BY: Claude
NEXT_CONTROL: advisory_request.md CONTROL_SEQ 1171

---

# 2026-04-28 M50 Axis 3b — preference-not-applied 버튼 + dist + E2E 검증

## 이번 라운드 범위

프론트엔드 + dist + E2E —
`app/frontend/src/api/client.ts`, `app/frontend/src/components/MessageBubble.tsx`,
`app/frontend/src/components/ChatArea.tsx`, `app/frontend/src/App.tsx`,
`app/static/dist/assets/index.js`, `app/static/dist/assets/index.css`,
`e2e/tests/web-smoke.spec.mjs`.

backend / storage / approval 변경 없음.
`docs/MILESTONES.md` 미수정 (handoff 경계 — M51 advisory 후 doc-sync에서 처리).

## 직접 실행 결과

| 체크 | 결과 |
|------|------|
| `tsc --noEmit` | **EXIT: 0** |
| `git diff --check` (7개 파일) | **PASS** (exit 0) |
| dist `grep -c "preference-not-applied-btn" index.js` | **1** |
| Playwright 격리 실행 (구현자 보고) | **1 passed (9.2s)** |

## 구현 클레임 확인

| 클레임 | 확인 결과 |
|--------|---------|
| `client.ts:98` `postPreferenceExplicitCorrection(sessionId, messageId, fingerprint)` → `POST /api/preferences/record-correction` | ✓ |
| `MessageBubble.tsx:57` `onPrefCorrection?: (fingerprint, messageId) => void` Props 추가 | ✓ |
| `MessageBubble.tsx:565–571` `preference-not-applied-btn` 버튼, `onPrefCorrection(pref.fingerprint, message.message_id)` 호출 | ✓ |
| `ChatArea.tsx:33,58,148` `onPrefCorrection` prop 전달 체인 | ✓ |
| `App.tsx:15,56–60,203` `handlePrefCorrection` — `postPreferenceExplicitCorrection(chat.sessionId, ...)` + toast on error | ✓ |
| dist `assets/index.js`에 `preference-not-applied-btn` testid 포함 | ✓ (grep 1건) |
| `e2e/tests/web-smoke.spec.mjs:12258` 신규 시나리오 — `record-correction` route 호출 검증 | ✓ |
| storage / backend / approval 미수정 | ✓ |
| commit / push / PR 미실행 | ✓ |

## M50 완성 상태

| Axis | 내용 | 상태 |
|------|------|------|
| 1 | PreferencePanel sidebar "이번 응답 반영" 배지 + dist + E2E | ✓ PR #49 |
| 2 | corrected_count 집계 범위 확장 (chat 교정 포함) | ✓ PR #49 |
| 3 | 명시적 교정 backend endpoint (`/api/preferences/record-correction`) | ✓ PR #49 |
| 3b | 프론트엔드 `반영 안 됨` 버튼 + dist + E2E | ✓ 이번 라운드 |

## Dirty Tree 상태

| 파일 | 상태 | 라운드 |
|------|------|--------|
| `app/frontend/src/api/client.ts` | 수정됨, 미커밋 | M50 Axis 3b |
| `app/frontend/src/components/MessageBubble.tsx` | 수정됨, 미커밋 | M50 Axis 3b |
| `app/frontend/src/components/ChatArea.tsx` | 수정됨, 미커밋 | M50 Axis 3b |
| `app/frontend/src/App.tsx` | 수정됨, 미커밋 | M50 Axis 3b |
| `app/static/dist/assets/index.js` | 수정됨, 미커밋 | M50 Axis 3b |
| `app/static/dist/assets/index.css` | 수정됨, 미커밋 | M50 Axis 3b |
| `e2e/tests/web-smoke.spec.mjs` | 수정됨, 미커밋 | M50 Axis 3b |

현재 브랜치: `feat/m50-axis1-axis2-pref-visibility` (PR #49)
HEAD: `a915399` (M50 Axis 3 backend)

## 다음 행동

M50 전체 완료 (Axis 1–3b). 7개 파일 커밋+푸시 후 M51 방향 advisory.
→ `advisory_request.md` CONTROL_SEQ 1171 — M51 첫 슬라이스 방향 결정.
