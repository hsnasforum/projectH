# 2026-04-26 M47 reliability signal badge

## 변경 파일
- `app/handlers/preferences.py`
- `app/frontend/src/api/client.ts`
- `app/frontend/src/components/PreferencePanel.tsx`
- `tests/test_preference_handler.py`
- `work/4/26/2026-04-26-m47-reliability-signal-badge.md`

## 사용 skill
- `work-log-closeout`: 구현 변경 파일, 실제 검증, 남은 리스크를 한국어 closeout으로 남겼다.

## 변경 이유
- M45의 `reliability_stats`와 M46의 `quality_info.is_high_quality`를 함께 사용해, 여러 번 적용되고 거의 교정되지 않은 선호를 사용자에게 더 명확하게 보여주기 위한 M47 Axis 1 handoff를 수행했다.
- 기존 `reliability_stats` / `quality_info` 구조와 panel-level `고품질 N개` 집계는 유지하면서 per-card 표시만 추가하는 범위였다.

## 핵심 변경
- `app/handlers/preferences.py`에 `_is_highly_reliable_preference()` helper를 추가해 `quality_info.is_high_quality is True`, `applied_count >= 3`, `corrected_count / applied_count < 0.15` 조건을 모두 만족할 때만 `is_highly_reliable: True`를 붙였다.
- 모든 enriched preference에 `is_highly_reliable` boolean을 기본적으로 계산하도록 했다.
- `PreferenceRecord` 타입에 `is_highly_reliable?: boolean | null`을 추가했다.
- `PreferencePanel`의 기존 `고품질` 배지 근처에 `is_highly_reliable === true`일 때만 `신뢰도 높음` 배지를 렌더링하도록 했다.
- `tests/test_preference_handler.py`에 true case, `applied_count < 3`, correction rate `>= 0.15`, `is_high_quality is None` false case를 한 테스트로 추가했다.

## 검증
- `sha256sum .pipeline/implement_handoff.md` 확인: `63d0dadc5790f37dc4904f9a2ac80eb2469c5a4b448daea0043422800fcf5f95`.
- `python3 -m py_compile app/handlers/preferences.py` 통과.
- `python3 -m unittest -v tests.test_preference_handler` 통과: 16 tests OK.
- `cd app/frontend && npx tsc --noEmit` 통과.
- `git diff --check -- app/handlers/preferences.py app/frontend/src/api/client.ts app/frontend/src/components/PreferencePanel.tsx tests/test_preference_handler.py` 통과.
- `git diff --no-index --check /dev/null work/4/26/2026-04-26-m47-reliability-signal-badge.md`는 신규 파일 diff exit 1 특성을 감안해 whitespace 출력 없음으로 확인했다.

## 남은 리스크
- 브라우저 smoke나 스크린샷 검증은 실행하지 않았다. 이번 handoff의 프론트 검증은 TypeScript typecheck와 조건부 렌더링 코드 확인까지로 제한했다.
- docs/MILESTONES doc-sync는 handoff boundary상 이번 slice에서 제외했다.
- PR #38 / PR #39는 여전히 operator merge gate 상태이며, 이번 라운드에서 commit, push, PR publish, merge는 수행하지 않았다.
