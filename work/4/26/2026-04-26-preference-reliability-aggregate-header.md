# 2026-04-26 preference reliability aggregate header

## 변경 파일
- `app/handlers/preferences.py`
- `app/frontend/src/api/client.ts`
- `app/frontend/src/components/PreferencePanel.tsx`
- `tests/test_preference_handler.py`
- `work/4/26/2026-04-26-preference-reliability-aggregate-header.md`

## 사용 skill
- `work-log-closeout`: 구현 파일, 실제 검증, 남은 리스크를 한국어 closeout으로 남겼다.

## 변경 이유
- per-preference `reliability_stats.applied_count` / `corrected_count`는 이미 응답과 카드 상세에 있었지만, 패널 상단에서 전체 활성 선호의 적용/교정 총량을 빠르게 볼 수 없었다.
- 이번 slice는 M45 preference reliability aggregate header만 추가하며, M44 publish나 runtime/controller 변경은 범위 밖이다.

## 핵심 변경
- preferences list payload에 active preference만 합산한 `total_applied`, `total_corrected`를 추가했다.
- 기존 per-preference `reliability_stats` 구조와 카드별 "적용 N회 · 교정 N회" 표시는 그대로 유지했다.
- frontend `PreferencesPayload` 타입에 aggregate 필드를 optional로 추가했다.
- `PreferencePanel` header가 active preference가 있을 때 `총 적용 N회 · 총 교정 N회`를 기존 active/candidate count 아래 compact line으로 표시한다.
- handler 단위 테스트에 no-active aggregate zero와 mixed-status active-only 합산 케이스를 추가했다.

## 검증
- `python3 -m py_compile app/handlers/preferences.py` 통과.
- `python3 -m unittest -v tests.test_preference_handler` 통과: 14 tests.
- `cd app/frontend && npx tsc --noEmit` 통과.
- `git diff --check -- app/handlers/preferences.py tests/test_preference_handler.py app/frontend/src/api/client.ts app/frontend/src/components/PreferencePanel.tsx` 통과.

## 남은 리스크
- 브라우저 렌더링 smoke는 실행하지 않았다. 변경 범위가 기존 React header text와 타입/handler 응답에 한정되어 TSC와 handler unit으로 확인했다.
- M44 publish gate와 기존 runtime/controller dirty 변경은 이번 handoff 범위 밖이라 건드리지 않았다.
- M45 milestone/doc sync는 handoff boundary에 따라 이번 slice에서 수행하지 않았다.
