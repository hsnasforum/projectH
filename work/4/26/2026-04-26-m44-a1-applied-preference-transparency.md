# 2026-04-26 M44 A1 applied preference transparency

## 변경 파일
- `app/frontend/src/components/MessageBubble.tsx`

## 사용 skill
- `finalize-lite`: 구현 후 실행한 검증, 미실행 검증, doc-sync 보류 범위, closeout 준비 상태를 점검했다.
- `release-check`: 변경 파일과 실제 검증 결과가 handoff 범위에 맞는지 확인했다.
- `doc-sync`: 적용 선호 popover UI 계약 변경은 문서 동기화 대상이지만 이번 handoff가 문서 변경을 금지했음을 확인했다.
- `work-log-closeout`: 변경 파일, 실제 검증, 남은 리스크를 한국어 closeout으로 정리했다.

## 변경 이유
- M44 Axis 1 handoff는 assistant message의 applied preferences popover에서 반영 당시 선호가 현재 어떤 상태인지 더 잘 보이게 하도록 요구했다.
- 서버 payload와 preference 타입에는 이미 `status`, `last_transition_reason`이 있으므로, `MessageBubble.tsx` popover 표시만 확장하면 충분했다.

## 핵심 변경
- `app/frontend/src/components/MessageBubble.tsx:547` 부근에 status badge를 추가했다.
- `fullPref?.status`가 있고 `"active"`가 아닐 때만 badge를 렌더링하며, `"paused"`는 사용자 표시 문자열 `일시중지`로 보여준다.
- `app/frontend/src/components/MessageBubble.tsx:552` 부근에 `last_transition_reason` 표시를 추가했다.
- `fullPref?.last_transition_reason`이 있을 때만 `이유: ...` 문구를 표시한다.
- 기존 `displayDescription` span, edit/save 버튼, pause 버튼, `data-testid="applied-preferences-badge"`, `data-testid="applied-preferences-popover"`는 변경하지 않았다.

## 검증
- `sha256sum .pipeline/implement_handoff.md` 확인: `38376388abe45d20cf868ac354d6030f654d664c08e47a6b69e46e5b435c7b44`로 요청 handoff SHA와 일치.
- `cd app/frontend && npx tsc --noEmit` 통과, 출력 없음.
- `git diff --check -- app/frontend/src/components/MessageBubble.tsx` 통과, 출력 없음.
- `git diff -- app/frontend/src/components/MessageBubble.tsx`로 변경 범위가 handoff의 한 파일에 해당함을 확인했다.
- `git diff --check -- app/frontend/src/components/MessageBubble.tsx work/4/26/2026-04-26-m44-a1-applied-preference-transparency.md` 통과, 출력 없음.

## 남은 리스크
- browser/Playwright로 실제 popover 표시를 확인하지 않았다. sandbox 제약 및 handoff 기준에 따라 TypeScript 타입 체크로 대체했다.
- 전체 frontend test suite, browser/E2E, release gate는 실행하지 않았다.
- UI 계약 변경은 `docs/PRODUCT_SPEC.md`, `docs/ACCEPTANCE_CRITERIA.md` doc-sync 후보지만, 이번 handoff가 `docs/` 변경을 금지해 수정하지 않았다.
- 기존 작업트리의 untracked `report/gemini/**`, `verify/4/26/2026-04-26-b1-release-gate-pr35-reconcile.md`, `verify/4/26/2026-04-26-m43-publish-pr37-merge.md`, `work/4/26/2026-04-26-m43-publish-pr37-merge.md`, `work/4/26/2026-04-26-pr36-release-gate-merge.md`는 이번 handoff 범위 밖이므로 수정하지 않았다.
- commit, push, branch/PR 생성, merge는 수행하지 않았다.
