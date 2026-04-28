STATUS: verified
CONTROL_SEQ: 1163
BASED_ON_WORK: work/4/28/2026-04-28-m50-axis1-preference-panel-last-applied.md
BASED_ON_HANDOFF: .pipeline/implement_handoff.md CONTROL_SEQ 1163
VERIFIED_BY: Claude
NEXT_CONTROL: implement_handoff.md CONTROL_SEQ 1164

---

# 2026-04-28 M50 Axis 1 — PreferencePanel 이번 응답 반영 표시 검증

## 이번 라운드 범위

프론트엔드 소스 전용 — `app/frontend/src/App.tsx`, `app/frontend/src/components/Sidebar.tsx`,
`app/frontend/src/components/PreferencePanel.tsx`, `docs/MILESTONES.md`.

백엔드·approval·storage·dist 변경 없음. 브라우저/E2E 검증은 M50 Axis 2에서 수행.

## 직접 실행 결과

| 체크 | 결과 |
|------|------|
| `git diff --check` (4개 파일) | **PASS** (exit 0) |
| `python3 -m py_compile app/serializers.py app/handlers/chat.py` | **PASS** (exit 0) |
| `app/frontend/node_modules/.bin/tsc --noEmit --project app/frontend/tsconfig.json` | **PASS** (exit 0) |

## 구현 클레임 확인

| 클레임 | 확인 결과 |
|--------|---------|
| `App.tsx` line 106–115 — 마지막 assistant 메시지의 `applied_preferences` fingerprint 목록 역순 계산 | ✓ |
| `App.tsx` line 136 — `lastAppliedFingerprints={lastAppliedFingerprints}` Sidebar로 전달 | ✓ |
| `Sidebar.tsx` line 16 — `lastAppliedFingerprints?: string[]` Props 추가 | ✓ |
| `Sidebar.tsx` line 205 — `<PreferencePanel lastAppliedFingerprints={lastAppliedFingerprints ?? []} />` 전달 | ✓ |
| `PreferencePanel.tsx` line 32 — `PanelProps { lastAppliedFingerprints?: string[] }` 인터페이스 추가 | ✓ |
| `PreferencePanel.tsx` line 52 — `{ lastAppliedFingerprints = [] }: PanelProps` 기본값 처리 | ✓ |
| `PreferencePanel.tsx` line 211 — `appliedSet = new Set(lastAppliedFingerprints)` 생성 | ✓ |
| `PreferencePanel.tsx` line 368–375 — `status === "active" && appliedSet.has(delta_fingerprint ?? "")` 조건 + `data-testid="preference-last-applied-badge"` 배지 | ✓ |
| `docs/MILESTONES.md` line 1104–1109 — M50 Axis 1 ACTIVE 항목, dist 재빌드 미포함 명시 | ✓ |
| MessageBubble 미수정 (M48 구현) | ✓ |
| app/serializers.py / app/handlers/chat.py 미수정 | ✓ |
| approval / storage / preference lifecycle 미수정 | ✓ |
| commit / push / PR 미실행 | ✓ |

## Dirty Tree 상태

| 파일 | 상태 | 라운드 |
|------|------|--------|
| `app/frontend/src/App.tsx` | 수정됨, 미커밋 | M50 Axis 1 |
| `app/frontend/src/components/Sidebar.tsx` | 수정됨, 미커밋 | M50 Axis 1 |
| `app/frontend/src/components/PreferencePanel.tsx` | 수정됨, 미커밋 | M50 Axis 1 |
| `docs/MILESTONES.md` | 수정됨, 미커밋 | M49 Axis 1+2+3 + M50 Axis 1 누적 |

M49 Axis 3 소스 파일(`model_adapter/`, `core/agent_loop.py`, `tests/`)은 `f7e3e4d` 커밋에 포함됨.
PR #48은 M49 Axis 3 브랜치로 대기 중.

## 브라우저/dist 표면

**주의**: `app/static/dist/`는 M50 Axis 1 TypeScript 소스를 아직 반영하지 않음.
`preference-last-applied-badge` 배지는 현재 브라우저에서 보이지 않는다.
dist 재빌드 + Playwright 검증은 M50 Axis 2에서 수행.

## 다음 행동

M50 Axis 1 소스 검증 완료.
→ `implement_handoff.md` CONTROL_SEQ 1164 — dist 재빌드 + `preference-last-applied-badge` Playwright 시나리오 추가 및 격리 실행.
