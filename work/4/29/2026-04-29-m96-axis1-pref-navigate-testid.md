# 2026-04-29 M96 Axis 1 선호 카드 이동 링크 test id 추가

## 변경 파일

- `app/frontend/src/components/MessageBubble.tsx`
- `work/4/29/2026-04-29-m96-axis1-pref-navigate-testid.md`

## 사용 skill

- `finalize-lite`: 구현 라운드 종료 전 변경 파일, 실행 검증, doc-sync 필요 여부, `/work` closeout 준비 상태를 점검하기 위해 사용.
- `work-log-closeout`: 변경 파일, 실행 검증, 남은 리스크를 `/work` closeout 형식으로 정리하기 위해 사용.

## 변경 이유

- M95에서 추가한 applied preferences 팝오버의 `선호에서 보기` 링크만 `data-testid`가 없어, 같은 popover 안의 다른 인터랙티브 요소와 테스트 선택자 패턴이 맞지 않았다.
- 향후 E2E에서 해당 링크를 안정적으로 찾을 수 있도록 `data-testid="pref-navigate-to-card"`를 부여해야 했다.

## 핵심 변경

- `MessageBubble` applied preferences 팝오버의 `선호에서 보기` anchor에 `data-testid="pref-navigate-to-card"`를 추가했다.
- 링크의 `href`, class, popover 닫기 동작은 변경하지 않았다.
- `fullPref?.preference_id`가 있을 때만 링크를 표시하는 기존 조건도 유지했다.
- handoff 경계에 따라 `app/static/dist/`, `e2e/`, docs, `.pipeline` control 파일은 수정하지 않았다.

## 검증

- `git switch -c feat/m96-axis1-pref-navigate-testid`
  - 실패: `.git/refs/heads/feat/m96-axis1-pref-navigate-testid.lock` 생성이 `Read-only file system`으로 거부되어 브랜치를 만들 수 없었다.
- `bash -o pipefail -c 'cd app/frontend && npx tsc --noEmit 2>&1 | head -20'`
  - 통과. 출력 없음.
- `git diff --check -- app/frontend/src/components/MessageBubble.tsx`
  - 통과. 출력 없음.
- `git status --short -- app/static/dist e2e`
  - 통과. 출력 없음. 이번 handoff에서 `app/static/dist/`, `e2e/` 변경 없음.
- `git diff --stat -- app/frontend/src/components/MessageBubble.tsx app/static/dist e2e`
  - 확인: `MessageBubble.tsx` 1줄 추가.

## 남은 리스크

- 브라우저 E2E는 실행하지 않았다. 이번 handoff 검증 지시가 TypeScript 컴파일, diff check, dist/E2E 무변경 확인으로 한정되어 있었다.
- 새 selector는 source에만 추가했다. dist 재빌드는 이번 handoff 경계 밖이라 수행하지 않았다.
- 로컬 `.git/refs` 쓰기 제한 때문에 요청된 브랜치 생성은 실패했다. 커밋, push, PR 생성은 수행하지 않았다.
