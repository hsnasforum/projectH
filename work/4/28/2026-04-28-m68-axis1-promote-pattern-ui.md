# 2026-04-28 M68 Axis 1 promote-pattern UI

## 변경 파일
- `app/frontend/src/api/client.ts`
- `app/frontend/src/components/PreferencePanel.tsx`
- `storage/correction_store.py`
- `storage/sqlite_store.py`
- `app/handlers/aggregate.py`
- `app/web.py`
- `tests/test_correction_store.py`
- `tests/test_sqlite_store.py`

## 사용 skill
- `security-gate`: `POST /api/corrections/promote-pattern`가 local-first/same-origin 경계 안에서 기존 correction/preference store 전이와 idempotency 계약을 재사용하는지 점검했습니다.
- `work-log-closeout`: 이번 handoff 구현, 실제 검증, 브랜치 제한, 남은 리스크를 `/work` 형식으로 기록했습니다.

## 변경 이유
- CONTROL_SEQ 1237 handoff가 `CONFIRMED` correction pattern을 `PROMOTED` 상태와 PreferenceRecord 후보로 승격하는 backend 경로에 더해, `PreferencePanel`에서 운영자가 직접 누를 수 있는 `승격` 버튼과 frontend client 함수를 요구했습니다.

## 핵심 변경
- `promoteCorrectionPattern()` frontend API client를 추가해 `/api/corrections/promote-pattern` POST를 호출하도록 했습니다.
- `PreferencePanel`의 반복 교정 상단 액션에 `data-testid="correction-promote-pattern"` 버튼을 추가하고, 클릭 후 `load()`로 패널 데이터를 새로고침하도록 했습니다.
- JSON/SQLite correction store에 `promote_by_fingerprint()`를 추가해 `CONFIRMED` 상태 record만 `PROMOTED`로 전환하도록 했습니다.
- aggregate handler와 web router에 promote-pattern 서비스/POST dispatch를 추가했습니다.
- JSON/SQLite 단위 테스트에 confirmed-only promotion, `RECORDED`/`STOPPED` skip, missing fingerprint empty 반환 케이스를 추가했습니다.

## 검증
- `sha256sum .pipeline/implement_handoff.md` → `e90c85b2c7649b58f622579495aacb93ce9afc19e5124d5644bcb08d72b5b493` 일치
- `app/frontend/node_modules/.bin/tsc --noEmit --project app/frontend/tsconfig.json` → PASS
- `python3 -m py_compile storage/correction_store.py storage/sqlite_store.py app/handlers/aggregate.py app/web.py` → PASS
- `python3 -m unittest -v tests.test_correction_store` → PASS, 31 tests
- `python3 -m unittest -v tests.test_sqlite_store` → PASS, 35 tests
- `git diff --check -- app/frontend/src/api/client.ts app/frontend/src/components/PreferencePanel.tsx storage/correction_store.py storage/sqlite_store.py app/handlers/aggregate.py app/web.py tests/test_correction_store.py tests/test_sqlite_store.py` → PASS

## 남은 리스크
- `git switch -c feat/m68-axis1-promote-pattern origin/main`은 `.git/index.lock` 쓰기 제한으로 실패했습니다. commit/push/PR 생성은 수행하지 않았고, 현재 변경은 작업트리에만 남아 있습니다.
- handoff가 dist 재빌드를 금지했으므로 `app/frontend/dist`는 갱신하지 않았습니다.
- Playwright/E2E는 handoff 검증 기준에 없고 dist 재빌드 금지 범위와 맞물려 실행하지 않았습니다. 브라우저-visible 버튼은 TypeScript 검증까지만 수행했습니다.
