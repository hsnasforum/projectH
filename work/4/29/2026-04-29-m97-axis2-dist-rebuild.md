# 2026-04-29 M97 Axis 2 dist 재빌드

## 변경 파일

- `app/static/dist/assets/index.css`
- `app/static/dist/assets/index.js`
- `work/4/29/2026-04-29-m97-axis2-dist-rebuild.md`

## 사용 skill

- `work-log-closeout`: 변경 파일, 실행 검증, 남은 리스크를 구현 라운드 closeout 형식으로 정리하기 위해 사용했다.
- `finalize-lite`: dist-only 구현 후 검증 진실성, doc-sync 필요 여부, `/work` 준비 상태를 점검하기 위해 사용했다.

## 변경 이유

- M97 Axis 1에서 추가된 반복 교정 자동 활성화 알림 UX가 production dist에는 아직 반영되지 않았다.
- handoff가 지정한 범위에 따라 기존 Axis 1 dirty source를 유지한 채 `app/frontend` production build 결과만 `app/static/dist/`에 반영해야 했다.

## 핵심 변경

- `app/frontend`에서 `npx vite build`를 실행해 production bundle을 재생성했다.
- 빌드 결과로 `app/static/dist/assets/index.js`와 관련 CSS asset이 갱신됐다.
- dist JS에 `data-testid="preference-auto-activated-notice"` 문자열이 포함되는지 확인했다.
- React source, Python handler, docs, E2E source는 이번 Axis 2 라운드에서 추가 수정하지 않았다.
- `.pipeline/` control slot, commit, push, branch/PR publish는 수행하지 않았다.

## 검증

- `sha256sum .pipeline/implement_handoff.md`
  - 통과: `7adf41a2557853988c79276163bb8aaca901f5b0effcb0f3ec026a37ac362ce8` 일치.
- `npx vite build`
  - 통과. `app/static/dist/index.html`, `app/static/dist/assets/index.css`, `app/static/dist/assets/index.js`가 생성됐다.
  - Vite CJS Node API deprecation 경고가 출력됐지만 빌드는 성공했다.
- `ls -lh app/static/dist/assets/index.js`
  - 통과: `315K`.
- `grep -c "preference-auto-activated-notice" app/static/dist/assets/index.js`
  - 통과: `1`.
- `git diff --check -- app/static/dist/assets/index.js`
  - 통과.
- `git diff --check -- app/static/dist`
  - 통과.

## 남은 리스크

- E2E는 handoff에서 불필요하다고 명시되어 실행하지 않았다. 실제 브라우저 smoke는 별도 verify/CI 환경에서 확인해야 한다.
- 이번 라운드는 dist 재빌드만 수행했으므로 Axis 1의 기존 uncommitted source/docs/test 변경은 그대로 남아 있다.
