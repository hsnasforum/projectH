# 2026-04-29 M95 Axis 1 applied preferences 팝오버 선호 카드 이동 링크

## 변경 파일

- `app/frontend/src/components/MessageBubble.tsx`
- `app/frontend/src/components/PreferencePanel.tsx`
- `work/4/29/2026-04-29-m95-axis1-popover-navigate-to-preference.md`

## 사용 skill

- `finalize-lite`: 구현 라운드 종료 전 변경 파일, 실행 검증, doc-sync 필요 여부, `/work` closeout 준비 상태를 점검하기 위해 사용.
- `work-log-closeout`: 변경 파일, 실행 검증, 남은 리스크를 `/work` closeout 형식으로 정리하기 위해 사용.

## 변경 이유

- applied preferences 팝오버에는 반영된 선호 설명과 품질/신뢰도 신호가 표시되지만, 같은 선호를 관리하는 `PreferencePanel` 카드로 바로 이동하는 경로가 없었다.
- 팝오버에서 `fullPreferences`로 매칭되는 선호에 한해 관리 카드 anchor로 이동할 수 있게 해야 했다.

## 핵심 변경

- `PreferencePanel`의 `filteredPreferences.map` 카드 루트에 `id={`pref-card-${pref.preference_id}`}`를 추가했다.
- `MessageBubble` applied preferences 팝오버에서 `fullPref?.preference_id`가 있을 때만 `선호에서 보기` 링크를 표시하도록 추가했다.
- 링크는 `#pref-card-${fullPref.preference_id}`로 이동하고 클릭 시 팝오버를 닫는다.
- 기존 pause, correction, description edit 버튼과 `fullPref`가 없는 항목의 표시 동작은 변경하지 않았다.
- handoff 경계에 따라 `app/static/dist/`, `e2e/`, docs, `.pipeline` control 파일은 수정하지 않았다.

## 검증

- `git switch -c feat/m95-axis1-popover-navigate-to-preference`
  - 실패: `.git/refs/heads/feat/m95-axis1-popover-navigate-to-preference.lock` 생성이 `Read-only file system`으로 거부되어 브랜치를 만들 수 없었다.
- `bash -o pipefail -c 'cd app/frontend && npx tsc --noEmit 2>&1 | head -20'`
  - 통과. 출력 없음.
- `git diff --check -- app/frontend/src/components/MessageBubble.tsx app/frontend/src/components/PreferencePanel.tsx`
  - 통과. 출력 없음.
- `git status --short -- app/static/dist e2e`
  - 통과. 출력 없음. 이번 handoff에서 `app/static/dist/`, `e2e/` 변경 없음.
- `git diff --stat -- app/frontend/src/components/MessageBubble.tsx app/frontend/src/components/PreferencePanel.tsx app/static/dist e2e`
  - 확인: `MessageBubble.tsx` 9줄 추가, `PreferencePanel.tsx` 1줄 추가.

## 남은 리스크

- 브라우저 E2E는 실행하지 않았다. 이번 handoff 검증 지시가 TypeScript 컴파일, diff check, dist/E2E 무변경 확인으로 한정되어 있었다.
- UI에 새 이동 링크가 추가되었지만, handoff가 수정 허용 파일을 두 source 파일로 제한해 제품 문서는 수정하지 않았다.
- 로컬 `.git/refs` 쓰기 제한 때문에 요청된 브랜치 생성은 실패했다. 커밋, push, PR 생성은 수행하지 않았다.
