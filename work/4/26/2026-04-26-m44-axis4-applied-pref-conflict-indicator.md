# 2026-04-26 M44 Axis 4 applied preference conflict indicator

## 변경 파일
- `app/frontend/src/components/MessageBubble.tsx`
- `work/4/26/2026-04-26-m44-axis4-applied-pref-conflict-indicator.md`

## 사용 skill
- `work-log-closeout`: 변경 파일, 실제 검증, 남은 리스크를 한국어 closeout으로 남기는 데 사용했다.

## 변경 이유
- CONTROL_SEQ 365 handoff는 applied preferences popover에서 이미 fetch된 `fullPref.conflict_info.has_conflict`를 사용해 충돌 선호를 표시하라는 범위였다.
- `PreferencePanel`에는 conflict badge가 있지만, 응답에 실제 반영된 선호를 보여주는 `MessageBubble` popover에는 conflict indicator가 없었다.

## 핵심 변경
- `MessageBubble.tsx` applied preferences popover item에서 `fullPref?.conflict_info?.has_conflict === true` 여부를 계산한다.
- 값이 명시적으로 `true`일 때만 compact `⚠ 충돌` badge를 렌더링한다.
- badge는 description/edit row 뒤, non-active status badge 앞에 배치했다.
- 현재 `feat/watcher-turn-state`에는 PR #42 Axis 3 quality badge가 직접 반영되어 있지 않아, Axis 3 코드를 끌어오지 않고 이번 handoff의 conflict indicator만 추가했다.
- handoff boundary에 따라 server, runtime, stacked-branch feature, docs는 수정하지 않았다.

## 검증
- `sha256sum .pipeline/implement_handoff.md` 확인: `50aaf68edd9d321db71abc5e1053c6b4fa3610bd32864caf5d4e7699a7f89b1c`.
- `cd app/frontend && npx tsc --noEmit` 통과.
- `git diff --check -- app/frontend/src/components/MessageBubble.tsx` 통과.

## 남은 리스크
- browser smoke나 screenshot 검증은 실행하지 않았다. 이번 변경은 이미 typed된 optional field를 조건부 렌더링하는 UI-only slice라 TypeScript로 확인했다.
- PR #42의 quality badge와 이번 conflict badge의 최종 병합 순서는 PR stack retarget/merge 때 재확인해야 한다.
- commit, push, branch/PR publish, PR #38/#39/#40/#41/#42 merge는 수행하지 않았다.
