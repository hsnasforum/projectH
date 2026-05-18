# 2026-04-26 M48 conflict severity signal

## 변경 파일
- `app/handlers/preferences.py`
- `app/frontend/src/api/client.ts`
- `app/frontend/src/components/PreferencePanel.tsx`
- `tests/test_preference_handler.py`
- `work/4/26/2026-04-26-m48-conflict-severity-signal.md`

## 사용 skill
- `work-log-closeout`: 구현 변경 파일, 실제 검증, 남은 리스크를 한국어 closeout으로 남겼다.

## 변경 이유
- M47에서 per-preference `is_highly_reliable`가 추가됐지만, conflict payload는 충돌 존재 여부와 상대 id만 알려주고 reliable preference가 얽힌 충돌을 구분하지 못했다.
- CONTROL_SEQ 340 handoff는 기존 `has_conflict` / `conflicting_preference_ids` 의미를 유지하면서 `conflict_severity`를 추가하도록 제한했다.

## 핵심 변경
- `app/handlers/preferences.py`에서 enriched preferences의 `is_highly_reliable` lookup을 만들고, 모든 `conflict_info`에 `conflict_severity`를 추가했다.
- `conflict_severity`는 conflict가 없으면 `none`, 충돌 당사자나 상대 중 하나라도 `is_highly_reliable is True`이면 `high`, 나머지 충돌은 `normal`로 계산한다.
- `PreferenceRecord.conflict_info` 타입에 `conflict_severity?: "high" | "normal" | "none" | null`을 추가했다.
- `PreferencePanel`은 `conflict_severity === "high"`일 때만 conflict badge에 elevated amber 스타일을 적용하고, normal conflict badge는 기존 orange 스타일을 유지한다.
- `tests/test_preference_handler.py`에 both-high, one-high, neither-high, no-conflict severity case를 검증하는 focused test를 추가했다.

## 검증
- `sha256sum .pipeline/implement_handoff.md` 확인: `ccb6a8a147b07ba462d313e165a4936a88d254a1d43cd70b9370bef2bc5daa88`.
- `python3 -m py_compile app/handlers/preferences.py` 통과.
- `python3 -m unittest -v tests.test_preference_handler` 통과: 18 tests OK.
- `cd app/frontend && npx tsc --noEmit` 통과.
- `git diff --check -- app/handlers/preferences.py app/frontend/src/api/client.ts app/frontend/src/components/PreferencePanel.tsx tests/test_preference_handler.py` 통과.

## 남은 리스크
- browser smoke나 screenshot 검증은 실행하지 않았다. 이번 변경은 additive payload field와 조건부 badge styling이라 unit + TypeScript로 확인했다.
- M48 MILESTONES / PRODUCT_SPEC / ACCEPTANCE_CRITERIA doc-sync는 handoff boundary상 이번 slice에서 제외했다.
- PR #38 / PR #39 merge는 여전히 operator gate이며 이번 라운드에서 commit, push, PR publish, merge는 수행하지 않았다.
