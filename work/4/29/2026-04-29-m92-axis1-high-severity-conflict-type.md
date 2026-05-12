# 2026-04-29 M92 Axis 1 high_severity_conflict_count 타입 동기화

## 변경 파일

- `app/frontend/src/api/client.ts`
- `app/frontend/src/components/PreferencePanel.tsx`
- `work/4/29/2026-04-29-m92-axis1-high-severity-conflict-type.md`

## 사용 skill

- `work-log-closeout`: 이번 구현 라운드의 변경 파일, 실행 검증, 남은 리스크를 `/work` closeout 형식으로 정리하기 위해 사용.

## 변경 이유

- backend `list_preferences_payload()` 응답에는 `high_severity_conflict_count`가 포함되지만 frontend `PreferencesPayload` 타입에는 같은 필드가 없어 타입 계약이 어긋나 있었다.
- `PreferencePanel.tsx`는 이 타입 갭 때문에 `data as typeof data & { high_severity_conflict_count?: number | null }` 캐스트 우회책을 사용하고 있었다.

## 핵심 변경

- `PreferencesPayload`에 `high_severity_conflict_count?: number | null;`을 추가했다.
- `PreferencePanel`에서 `dataWithConflict` 타입 캐스트를 제거했다.
- `setHighSeverityConflictCount()`가 `data.high_severity_conflict_count`를 직접 읽도록 정리했다.
- 기존 fallback 계산인 active preference의 high conflict 필터링은 유지했다.
- handoff에서 금지한 `app/static/dist/`, `e2e/` 파일은 수정하지 않았다.

## 검증

- `git switch -c feat/m92-axis1-high-severity-conflict-type`
  - 실패: `.git/refs/heads/feat/m92-axis1-high-severity-conflict-type.lock` 생성이 `Read-only file system`으로 거부되어 브랜치를 만들 수 없었다.
- `bash -o pipefail -c 'cd app/frontend && npx tsc --noEmit 2>&1 | head -20'`
  - 통과. 출력 없음.
- `git diff --check -- app/frontend/src/api/client.ts app/frontend/src/components/PreferencePanel.tsx`
  - 통과.
- `git status --short -- app/static/dist e2e`
  - 출력 없음. `app/static/dist`, `e2e` 변경 없음.

## 남은 리스크

- 이번 변경은 TypeScript 타입 계약 정리와 캐스트 제거만 수행했다. production dist 재빌드와 E2E 실행은 handoff 경계 밖이라 수행하지 않았다.
- 브랜치 생성은 로컬 `.git/refs` 쓰기 제한 때문에 실패했다. 커밋, push, PR 생성은 수행하지 않았다.
