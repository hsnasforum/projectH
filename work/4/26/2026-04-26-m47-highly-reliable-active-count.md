# 2026-04-26 M47 highly reliable active count

## 변경 파일
- `app/handlers/preferences.py`
- `app/frontend/src/api/client.ts`
- `app/frontend/src/components/PreferencePanel.tsx`
- `tests/test_preference_handler.py`
- `work/4/26/2026-04-26-m47-highly-reliable-active-count.md`

## 사용 skill
- `work-log-closeout`: 구현 변경 파일, 실제 검증, 남은 리스크를 한국어 closeout으로 남겼다.

## 변경 이유
- M47 Axis 1에서 per-card `신뢰도 높음` badge가 추가됐지만, panel header에는 활성 선호 중 highly reliable 항목 수가 아직 표시되지 않았다.
- 이번 CONTROL_SEQ 330 handoff는 M46 `고품질 N개` header와 같은 방식으로 active-only `highly_reliable_active_count` aggregate를 추가하는 범위였다.

## 핵심 변경
- `app/handlers/preferences.py`에서 enriched active preferences 중 `is_highly_reliable is True`인 항목 수를 `highly_reliable_active_count`로 응답에 추가했다.
- `PreferencesPayload` 타입에 `highly_reliable_active_count?: number | null`을 추가했다.
- `PreferencePanel`에서 서버 aggregate가 있으면 사용하고, 없으면 visible active preferences의 `is_highly_reliable === true` 값을 fallback으로 계산하도록 했다.
- panel header에 `highlyReliableActiveCount > 0`일 때만 `신뢰도 높음 N개`를 기존 `고품질 N개` 옆에 표시하도록 했다.
- `tests/test_preference_handler.py`에 mixed active / candidate / false case와 no active highly-reliable case를 검증하는 focused test를 추가했다.

## 검증
- `sha256sum .pipeline/implement_handoff.md` 확인: `293e64b9a4b34e44cbbdc6a100283a3a6ee902340415f6988411853f2e0754b1`.
- `python3 -m py_compile app/handlers/preferences.py` 통과.
- `python3 -m unittest -v tests.test_preference_handler` 통과: 17 tests OK.
- `cd app/frontend && npx tsc --noEmit` 통과.
- `git diff --check -- app/handlers/preferences.py app/frontend/src/api/client.ts app/frontend/src/components/PreferencePanel.tsx tests/test_preference_handler.py` 통과.

## 남은 리스크
- browser smoke나 screenshot 검증은 실행하지 않았다. 이번 변경은 additive header text와 payload aggregate라 unit + TypeScript로 확인했다.
- MILESTONES / PRODUCT_SPEC / ACCEPTANCE_CRITERIA doc-sync는 handoff boundary상 이번 slice에서 제외했다.
- PR #38 / PR #39 merge는 여전히 operator gate이며 이번 라운드에서 commit, push, PR publish, merge는 수행하지 않았다.
