# 2026-04-26 M44 Axis 2 applied preference reliability popover

## 변경 파일
- `app/frontend/src/components/MessageBubble.tsx`
- `work/4/26/2026-04-26-m44-axis2-applied-pref-reliability-popover.md`

## 사용 skill
- `work-log-closeout`: 변경 파일, 실제 검증, 남은 리스크를 한국어 closeout으로 남기는 데 사용했다.

## 변경 이유
- CONTROL_SEQ 355 handoff는 applied preferences popover에서 이미 fetch된 `fullPref.reliability_stats`를 사용해 per-preference 적용/교정 횟수를 표시하라는 범위였다.
- 서버 payload와 타입에는 `reliability_stats.applied_count` / `corrected_count`가 이미 있어 서버 변경 없이 `MessageBubble.tsx` UI만 수정할 수 있었다.

## 핵심 변경
- applied preferences popover item에서 `fullPref?.reliability_stats?.applied_count`와 `corrected_count`를 읽도록 했다.
- `applied_count`가 양수인 finite number일 때만 `적용 N회 · 교정 M회` compact line을 렌더링한다.
- `corrected_count`가 숫자가 아니면 표시값을 0으로 fallback한다.
- 새 line은 기존 `last_transition_reason` 표시 뒤, 원본/교정 snippet detail 앞에 배치했다.
- handoff boundary에 따라 server handler, runtime, launcher, stacked-branch feature, docs는 수정하지 않았다.

## 검증
- `sha256sum .pipeline/implement_handoff.md` 확인: `e850c142381ee96a3daa974b04334e989e5d92596bfd70b35b5b250e6a721ebf`.
- `cd app/frontend && npx tsc --noEmit` 통과.
- `git diff --check -- app/frontend/src/components/MessageBubble.tsx` 통과.

## 남은 리스크
- browser smoke나 screenshot 검증은 실행하지 않았다. 이번 변경은 이미 typed된 optional field를 조건부 렌더링하는 UI-only slice라 TypeScript로 확인했다.
- commit, push, branch/PR publish, PR #38/#39/#40 merge는 수행하지 않았다.
