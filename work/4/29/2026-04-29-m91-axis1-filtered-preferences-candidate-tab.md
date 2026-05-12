# 2026-04-29 M91 Axis 1 후보 탭 filteredPreferences 연결

## 변경 파일

- `app/frontend/src/components/PreferencePanel.tsx`
- `work/4/29/2026-04-29-m91-axis1-filtered-preferences-candidate-tab.md`

## 사용 skill

- `work-log-closeout`: 이번 구현 라운드의 변경 파일, 실행 검증, 남은 리스크를 `/work` closeout 형식으로 정리하기 위해 사용.

## 변경 이유

- M90 Axis 1에서 `candidatePreferences` state와 `candidateCount` 연결은 완료됐지만, 후보 탭 렌더링에 쓰이는 `filteredPreferences`는 여전히 `preferences` 전체 목록에서 `status === "candidate"`만 필터링했다.
- `preferences`가 `list_all(limit=50)` 기반일 때 후보가 50개 범위 밖에 있으면 후보 탭 목록이 서버의 pre-filtered 후보 목록과 어긋날 수 있었다.

## 핵심 변경

- `statusFilter === "candidate"`이고 `candidatePreferences`가 존재하면 `filteredPreferences`가 `candidatePreferences`를 우선 사용하도록 변경했다.
- `all`, `active`, `paused` 필터는 기존 `preferences` 기반 동작을 유지했다.
- `candidatePreferences`가 `null`이면 기존 `preferences.filter(...)` 계산으로 fallback한다.
- handoff에서 금지한 `app/static/dist/`, `e2e/` 파일은 수정하지 않았다.

## 검증

- `git switch -c feat/m91-axis1-filtered-preferences-candidate-tab`
  - 실패: `.git/refs/heads/feat/m91-axis1-filtered-preferences-candidate-tab.lock` 생성이 `Read-only file system`으로 거부되어 브랜치를 만들 수 없었다.
- `bash -o pipefail -c 'cd app/frontend && npx tsc --noEmit 2>&1 | head -20'`
  - 통과. 출력 없음.
- `git diff --check -- app/frontend/src/components/PreferencePanel.tsx`
  - 통과.
- `git status --short -- app/static/dist e2e`
  - 출력 없음. `app/static/dist`, `e2e` 변경 없음.

## 남은 리스크

- 이번 변경은 후보 탭 렌더링 소스 선택만 조정했다. production dist 재빌드와 E2E 재실행은 handoff 경계 밖이라 수행하지 않았다.
- 브랜치 생성은 로컬 `.git/refs` 쓰기 제한 때문에 실패했다. 커밋, push, PR 생성은 수행하지 않았다.
