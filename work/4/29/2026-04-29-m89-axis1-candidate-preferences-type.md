# 2026-04-29 M89 Axis 1 candidate_preferences TypeScript 타입 동기화

## 변경 파일

- `app/frontend/src/api/client.ts`
- `work/4/29/2026-04-29-m89-axis1-candidate-preferences-type.md`

## 사용 skill

- `work-log-closeout`: 이번 구현 라운드의 변경 파일, 실행 검증, 남은 리스크를 `/work` closeout 형식으로 정리하기 위해 사용.

## 변경 이유

- M88에서 backend `list_preferences_payload()`가 `candidate_preferences`를 포함하도록 확장되었지만 frontend `PreferencesPayload` 타입에는 같은 키가 없어 타입 계약이 맞지 않았다.
- 이번 handoff 범위는 backend payload 키를 frontend TypeScript 타입에 반영하는 것만이었다.

## 핵심 변경

- `PreferencesPayload`에 `candidate_preferences?: PreferenceRecord[] | null;`를 추가했다.
- 기존 `preferences`, count, aggregate 필드 순서와 의미는 변경하지 않았다.
- handoff에서 금지한 React 컴포넌트, `app/static/dist/`, `e2e/` 파일은 수정하지 않았다.
- `high_severity_conflict_count`는 현재 타입에 존재하지 않았고 handoff가 새로 추가하지 말라고 명시했으므로 변경하지 않았다.

## 검증

- `git switch -c feat/m89-axis1-candidate-preferences-type`
  - 실패: `.git/refs/heads/feat/m89-axis1-candidate-preferences-type.lock` 생성이 `Read-only file system`으로 거부되어 브랜치를 만들 수 없었다.
- `python3 -m py_compile app/handlers/preferences.py`
  - 통과.
- `bash -o pipefail -c 'cd app/frontend && npx tsc --noEmit 2>&1 | head -20'`
  - 통과. 출력 없음.
- `git diff --check -- app/frontend/src/api/client.ts`
  - 통과.
- `git status --short -- app/frontend/src/api/client.ts app/static/dist e2e`
  - `app/frontend/src/api/client.ts`만 수정됨. `app/static/dist`, `e2e` 변경 없음.

## 남은 리스크

- 이번 변경은 타입 계약 동기화만 수행했다. `candidate_preferences`를 실제 UI에서 소비하거나 표시하는 작업은 포함하지 않았다.
- 브랜치 생성은 로컬 `.git/refs` 쓰기 제한 때문에 실패했다. 커밋, push, PR 생성은 수행하지 않았다.
