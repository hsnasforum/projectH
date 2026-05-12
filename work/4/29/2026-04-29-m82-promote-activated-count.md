# 2026-04-29 M82 promote activated count

## 변경 파일

- `app/handlers/corrections.py`
- `app/frontend/src/api/client.ts`
- `work/4/29/2026-04-29-m82-promote-activated-count.md`

## 사용 skill

- `work-log-closeout`: 구현 라운드 종료 기록에 필요한 변경 파일, 실제 검증, 남은 리스크를 정리하기 위해 사용했습니다.

## 변경 이유

- M82 handoff가 `promote_correction_pattern` 응답에 실제로 활성화된 preference 수를 드러내는 `activated_count`를 추가하도록 지정했습니다.
- M81에서 auto-activate 동작은 추가됐지만 응답에는 `promoted_count`만 있어 client가 활성화 결과를 관찰하기 어려웠습니다.

## 핵심 변경

- `promote_correction_pattern`에서 `activated_count`를 0으로 초기화하고, `activate_preference()`가 실제 record를 반환한 경우에만 증가시키도록 했습니다.
- 응답 dict에 `"activated_count": activated_count`를 추가했습니다.
- `app/frontend/src/api/client.ts`의 `promoteCorrectionPattern()` Promise 반환 타입과 `res.json()` cast에 `activated_count?: number`를 추가했습니다.
- `PreferencePanel.tsx` 렌더링과 dist 산출물은 handoff 경계에 따라 수정하지 않았습니다.

## 검증

- `sha256sum .pipeline/implement_handoff.md`: `3d49a96077a072b32463a68e285b1f4fceb6f82cb2d69c50bbc9253cd4d90980` 일치 확인.
- `git switch -c feat/m82-axis1-activate-count`: 실패. `.git/refs/heads/...` lock 생성이 read-only file system으로 거부되었습니다.
- `python3 -m py_compile app/handlers/corrections.py`: 통과.
- `app/frontend/node_modules/.bin/tsc --noEmit --project app/frontend/tsconfig.json`: 통과.
- `python3 -m unittest tests.test_smoke 2>&1 | tail -3`: 통과. `Ran 150 tests in 3.653s`, `OK`.
- `git diff --check -- app/handlers/corrections.py app/frontend/src/api/client.ts`: 통과.

## 남은 리스크

- 브랜치 생성이 sandbox의 `.git/refs` read-only 제한으로 실패해 변경은 `feat/m81-promote-auto-activate` dirty worktree에 남아 있습니다.
- UI 표시 변경과 dist 재빌드는 handoff 범위를 넘기지 않기 위해 실행하지 않았습니다.
- E2E와 broad unittest는 실행하지 않았습니다. 이번 변경은 backend 응답 필드와 frontend 타입 노출에 한정했고, `test_smoke`와 `tsc`로 좁게 검증했습니다.
- commit, push, PR 생성은 implement 역할 경계에 따라 수행하지 않았습니다.
