# 2026-04-29 M83 promote result UI

## 변경 파일

- `app/frontend/src/components/PreferencePanel.tsx`
- `work/4/29/2026-04-29-m83-promote-result-ui.md`

## 사용 skill

- `frontend-skill`: 운영형 앱 UI 변경이므로 기존 panel 흐름 안에서 작고 읽기 쉬운 인라인 상태 표시로 제한하기 위해 확인했습니다.
- `work-log-closeout`: 구현 라운드 종료 기록에 필요한 변경 파일, 실제 검증, 남은 리스크를 정리하기 위해 사용했습니다.

## 변경 이유

- M83 handoff가 M81 auto-activate와 M82 `activated_count` 응답을 사용해 승격 클릭 결과를 `PreferencePanel` 안에 인라인으로 표시하도록 지정했습니다.
- 기존 승격 버튼은 클릭 후 `load()`만 호출해 실제 승격/활성화 결과를 UI에서 확인하기 어려웠습니다.

## 핵심 변경

- `lastPromoteResult` 상태를 추가해 마지막 승격 결과의 `promoted`와 `activated` 값을 보관합니다.
- `promoteCorrectionPattern()` 호출 결과를 캡처하고 `promoted_count`, `activated_count`를 상태에 저장하도록 클릭 핸들러를 갱신했습니다.
- 승격 버튼 직후 `data-testid="correction-promote-result"` span을 렌더링해 활성화 수 또는 `패턴 없음`을 표시합니다.
- `app/static/dist/`는 handoff 경계에 따라 재빌드하지 않았습니다.

## 검증

- `sha256sum .pipeline/implement_handoff.md`: `229e0b1d2a14a5628da3bc503e8063f58d1fe202763f80435b1f13fe35ea28e8` 일치 확인.
- `git switch -c feat/m83-axis1-promote-result-ui`: 실패. `.git/refs/heads/...` lock 생성이 read-only file system으로 거부되었습니다.
- `app/frontend/node_modules/.bin/tsc --noEmit --project app/frontend/tsconfig.json`: 통과.
- `git diff --check -- app/frontend/src/components/PreferencePanel.tsx`: 통과.

## 남은 리스크

- 브랜치 생성이 sandbox의 `.git/refs` read-only 제한으로 실패해 변경은 `feat/m82-activate-count` dirty worktree에 남아 있습니다.
- dist 재빌드와 E2E는 handoff 범위를 넘기지 않기 위해 실행하지 않았습니다.
- 이번 변경은 frontend-only 타입 검증으로 확인했으며, browser smoke는 handoff 검증 기준에 없어 실행하지 않았습니다.
- commit, push, PR 생성은 implement 역할 경계에 따라 수행하지 않았습니다.
