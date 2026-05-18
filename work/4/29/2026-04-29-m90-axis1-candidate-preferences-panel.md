# 2026-04-29 M90 Axis 1 candidate_preferences PreferencePanel 연결

## 변경 파일

- `app/frontend/src/components/PreferencePanel.tsx`
- `work/4/29/2026-04-29-m90-axis1-candidate-preferences-panel.md`

## 사용 skill

- `work-log-closeout`: 이번 구현 라운드의 변경 파일, 실행 검증, 남은 리스크를 `/work` closeout 형식으로 정리하기 위해 사용.

## 변경 이유

- M88/M89에서 backend payload와 frontend 타입에 추가된 `candidate_preferences`가 `PreferencePanel.tsx` 상태에는 아직 연결되지 않았다.
- 후보 수 카운트가 서버의 pre-filtered 후보 목록을 우선 사용하도록 handoff 범위 안에서 타입 안전하게 연결할 필요가 있었다.

## 핵심 변경

- `PreferencePanel`에 `candidatePreferences` 상태를 추가했다.
- `load()`에서 `fetchPreferences()` 응답의 `data.candidate_preferences ?? null`을 상태에 저장했다.
- 헤더와 후보 탭에 쓰이는 `candidateCount`가 `candidatePreferences`가 있으면 그 길이를 우선 사용하고, 없으면 기존 `preferences.filter(...)` 계산으로 fallback하도록 바꿨다.
- 기존 preference 목록 렌더링과 status filter 동작은 변경하지 않았다.
- handoff에서 금지한 `app/static/dist/`, `e2e/` 파일은 수정하지 않았다.

## 검증

- `git switch -c feat/m90-axis1-candidate-preferences-panel`
  - 실패: `.git/refs/heads/feat/m90-axis1-candidate-preferences-panel.lock` 생성이 `Read-only file system`으로 거부되어 브랜치를 만들 수 없었다.
- `bash -o pipefail -c 'cd app/frontend && npx tsc --noEmit 2>&1 | head -20'`
  - 통과. 출력 없음.
- `git diff --check -- app/frontend/src/components/PreferencePanel.tsx`
  - 통과.
- `git status --short -- app/static/dist e2e`
  - 출력 없음. `app/static/dist`, `e2e` 변경 없음.

## 남은 리스크

- 이번 변경은 후보 수 계산에 서버 pre-filtered 후보 목록을 연결하는 범위만 수행했다. 후보 목록 렌더링 자체를 `candidate_preferences` 기반으로 바꾸는 작업은 포함하지 않았다.
- 브랜치 생성은 로컬 `.git/refs` 쓰기 제한 때문에 실패했다. 커밋, push, PR 생성은 수행하지 않았다.
