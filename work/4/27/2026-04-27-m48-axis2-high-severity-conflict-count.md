# 2026-04-27 M48 Axis 2 high severity conflict count

## 변경 파일
- `app/handlers/preferences.py`
- `app/frontend/src/components/PreferencePanel.tsx`
- `work/4/27/2026-04-27-m48-axis2-high-severity-conflict-count.md`

## 사용 skill
- `work-log-closeout`: 구현 변경 파일, 실제 검증, 남은 리스크를 한국어 closeout으로 남기는 데 사용했다.

## 변경 이유
- CONTROL_SEQ 495 handoff는 `origin/main`의 `conflict_severity` 필드를 전제로, 활성 선호 중 high severity conflict 개수를 PreferencePanel 헤더에 표시하라고 지정했다.
- sandbox에서 git index write가 막혀 브랜치 전환은 하지 않고, `origin/main` 파일 내용을 읽은 뒤 현재 파일 두 개를 in-place로 맞추는 방식으로 진행했다.

## 핵심 변경
- `app/handlers/preferences.py`에 `high_severity_conflict_count` 집계를 추가했다.
- 활성 선호만 대상으로 `conflict_info.conflict_severity == "high"`인 항목을 집계하고 `/api/preferences` payload에 포함했다.
- `PreferencePanel` 헤더의 active aggregate 줄에 `충돌 위험 N건` 표시를 추가하고 `data-testid="high-severity-conflict-count"`를 붙였다.
- 현재 브랜치의 `app/frontend/src/api/client.ts`는 handoff 범위 밖이라 수정하지 않았고, 컴포넌트 내부 타입 보강으로 `origin/main` 신호 payload를 읽도록 처리했다.

## 검증
- `sha256sum .pipeline/implement_handoff.md` 확인: `f1d584e3f486e07226d6829677bf42367a863d6010e0838803c8c06db6efb622`.
- `git show origin/main:app/handlers/preferences.py | grep -n "conflict_severity\|high_quality_active_count\|highly_reliable_active_count\|total_applied"`로 prerequisite 확인.
- `python3 -m py_compile app/handlers/preferences.py` 통과.
- `python3 -m unittest -v tests/test_preference_injection.py` 통과: 9 tests OK.
- `git diff --check -- app/handlers/preferences.py app/frontend/src/components/PreferencePanel.tsx` 통과.
- `python3 -m unittest -v tests/test_preference_handler.py` 통과: 14 tests OK.
- `cd app/frontend && npx tsc --noEmit` 통과.
- `cd e2e && npx playwright test tests/web-smoke.spec.mjs -g "preference" --reporter=line`은 matching test 0건으로 실패했다.
- `cd e2e && npx playwright test web-smoke.spec.mjs -g "선호|preference|충돌|신뢰" --reporter=line` 통과: 2 passed.

## 남은 리스크
- 이번 implement lane에서는 commit, push, branch/PR publish를 하지 않았다.
- handoff 경계에 따라 `docs/`, `verify/`, `.pipeline/`은 수정하지 않았다.
- 현재 브랜치는 `feat/watcher-turn-state` 그대로이며, 두 구현 파일은 `origin/main` 기준 신호 로직을 in-place로 반영한 상태다.
