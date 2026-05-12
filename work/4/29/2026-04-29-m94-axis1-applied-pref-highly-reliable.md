# 2026-04-29 M94 Axis 1 applied preferences 신뢰도 높음 배지

## 변경 파일

- `app/frontend/src/components/MessageBubble.tsx`
- `work/4/29/2026-04-29-m94-axis1-applied-pref-highly-reliable.md`

## 사용 skill

- `work-log-closeout`: 이번 구현 라운드의 변경 파일, 실행 검증, 남은 리스크를 `/work` closeout 형식으로 정리하기 위해 사용.

## 변경 이유

- `PreferencePanel` 선호 목록에는 `is_highly_reliable` 상태가 표시되지만, 메시지 응답의 `선호 N건 반영` 팝오버에는 같은 상태가 표시되지 않았다.
- applied preferences 팝오버에서도 반영된 선호의 신뢰도 높은 상태를 확인할 수 있게 해야 했다.

## 핵심 변경

- `MessageBubble` applied preferences 팝오버에서 `fullPref?.is_highly_reliable === true`를 `isHighlyReliable`로 계산하도록 추가했다.
- 각 applied preference 항목에서 `isHighlyReliable`일 때 `신뢰도 높음` 배지를 표시하도록 추가했다.
- 기존 `고품질`, reliability stats, conflict 표시, pause/edit/correction 버튼 동작은 변경하지 않았다.
- handoff에서 금지한 `app/static/dist/`, `e2e/` 파일은 수정하지 않았다.

## 검증

- `git switch -c feat/m94-axis1-applied-pref-highly-reliable`
  - 실패: `.git/refs/heads/feat/m94-axis1-applied-pref-highly-reliable.lock` 생성이 `Read-only file system`으로 거부되어 브랜치를 만들 수 없었다.
- `bash -o pipefail -c 'cd app/frontend && npx tsc --noEmit 2>&1 | head -20'`
  - 통과. 출력 없음.
- `git diff --check -- app/frontend/src/components/MessageBubble.tsx`
  - 통과.
- `git status --short -- app/static/dist e2e`
  - 출력 없음. `app/static/dist`, `e2e` 변경 없음.

## 남은 리스크

- 이번 변경은 source UI 컴포넌트만 수정했다. production dist 재빌드와 E2E 실행은 handoff 경계 밖이라 수행하지 않았다.
- 브랜치 생성은 로컬 `.git/refs` 쓰기 제한 때문에 실패했다. 커밋, push, PR 생성은 수행하지 않았다.
