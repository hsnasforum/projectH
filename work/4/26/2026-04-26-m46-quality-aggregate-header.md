# 2026-04-26 M46 quality aggregate header

## 변경 파일
- `app/handlers/preferences.py`
- `app/frontend/src/api/client.ts`
- `app/frontend/src/components/PreferencePanel.tsx`
- `tests/test_preference_handler.py`
- `work/4/26/2026-04-26-m46-quality-aggregate-header.md`

## 사용 skill
- `work-log-closeout`: 변경 파일, 실제 검증, 남은 리스크를 한국어 closeout으로 남겼다.

## 변경 이유
- preference card별 `고품질` badge는 있었지만, `PreferencePanel` header에서 활성 선호 중 고품질 선호가 몇 개인지 한눈에 볼 수 없었다.
- 이번 handoff는 M46 Axis 1 high-quality active preference count만 추가하며, quality scoring 자체나 M46 문서 동기화는 범위 밖이다.

## 핵심 변경
- `list_preferences_payload()` 응답에 `high_quality_active_count`를 추가했다.
- count 기준은 enriched preference 중 `status == "active"`이고 `quality_info.is_high_quality is True`인 항목으로 제한했다.
- frontend `PreferencesPayload` 타입에 optional `high_quality_active_count` 필드를 추가했다.
- `PreferencePanel` header의 reliability aggregate line에 `고품질 N개`를 함께 표시하되, 0일 때는 렌더링하지 않는다.
- 기존 per-card `고품질` badge 조건은 그대로 유지했다.
- handler focused test에 mixed active/candidate/paused와 no active high-quality 케이스를 추가했다.

## 검증
- `sha256sum .pipeline/implement_handoff.md` 확인: `0a3b5d275330d232afbde1fd6308c975df0e1baeb533c00d2305ff01fdd021d7`.
- `python3 -m py_compile app/handlers/preferences.py` 통과.
- `python3 -m unittest -v tests.test_preference_handler` 통과: 15 tests.
- `cd app/frontend && npx tsc --noEmit` 통과.
- `git diff --check -- app/handlers/preferences.py app/frontend/src/api/client.ts app/frontend/src/components/PreferencePanel.tsx tests/test_preference_handler.py` 통과.

## 남은 리스크
- browser smoke는 실행하지 않았다. 변경 범위가 기존 `PreferencePanel` header text, API response field, TypeScript 타입, handler focused test에 한정되어 unit/TSC로 확인했다.
- M46 `docs/MILESTONES.md` / product doc sync는 handoff boundary에서 별도 라운드로 분리되어 이번 slice에서 수행하지 않았다.
- PR #38 / PR #39 merge, commit, push, PR publish는 수행하지 않았다.
