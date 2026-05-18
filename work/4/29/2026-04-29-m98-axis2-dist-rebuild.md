# 2026-04-29 M98 Axis 2 dist 재빌드

## 변경 파일

- `app/static/dist/assets/index.js`
- `app/static/dist/assets/index.css`
- `work/4/29/2026-04-29-m98-axis2-dist-rebuild.md`

## 사용 skill

- `finalize-lite`: dist 재빌드 후 실제 검증 결과와 미실행 항목을 정리했다.
- `work-log-closeout`: 변경 파일, 실행 명령, 남은 리스크를 현재 `/work` 형식으로 기록했다.

## 변경 이유

- M98 Axis 1 교정 이력 상세 조회 변경을 production dist 산출물에 반영하기 위해 `app/frontend` Vite 빌드를 실행했다.
- 현재 dirty 트리의 Axis 1 uncommitted 파일은 유지하고, 이번 라운드는 dist 산출물만 추가 갱신했다.

## 핵심 변경

- `cd app/frontend && npx vite build`로 production 번들을 재생성했다.
- `app/static/dist/assets/index.js`에 `correction-detail-panel` testid가 포함된 것을 확인했다.
- 새 상세 패널 스타일에 필요한 Tailwind 유틸리티가 반영되며 `app/static/dist/assets/index.css`도 함께 갱신됐다.

## 검증

- 통과: `cd app/frontend && npx vite build`
  - 참고: Vite CJS Node API deprecation warning이 출력됐지만 빌드는 성공했다.
- 통과: `ls -lh app/static/dist/assets/index.js` → `318K`
- 통과: `grep -c "correction-detail-panel" app/static/dist/assets/index.js` → `1`
- 통과: `git diff --check -- app/static/dist/assets/index.js`
- 통과: `git diff --check -- app/static/dist/assets/index.js app/static/dist/assets/index.css`
- 미실행: Playwright E2E는 handoff에서 로컬 실행 불필요 및 CI 처리로 지정되어 실행하지 않았다.

## 남은 리스크

- `app/static/dist/assets/index.css`는 handoff의 “및 관련 assets” 범위에 따라 빌드 산출물로 함께 변경됐다.
- Axis 1 소스 파일과 E2E spec은 이전 라운드 dirty 상태를 유지했으며, 이번 라운드에서 React 소스 추가 수정은 하지 않았다.
- 브라우저 smoke 실제 실행은 CI에서 확인해야 한다.
