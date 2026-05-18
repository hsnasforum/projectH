# 2026-04-28 M69 Axis 1 correction search conflict

## 변경 파일
- `storage/correction_store.py`
- `storage/sqlite_store.py`
- `app/handlers/aggregate.py`
- `app/web.py`
- `app/frontend/src/api/client.ts`
- `app/frontend/src/components/PreferencePanel.tsx`
- `tests/test_correction_store.py`
- `tests/test_sqlite_store.py`

## 사용 skill
- `work-log-closeout`: 이번 implement 라운드의 변경 파일, 실제 검증, 브랜치 제한, 남은 리스크를 `/work` 형식으로 기록했습니다.

## 변경 이유
- M69 Axis 1 handoff에 따라 운영자가 교정 목록에서 오래된 correction을 검색/필터링하고, 이미 활성화된 preference와 같은 fingerprint를 가진 correction을 목록에서 바로 식별할 수 있어야 했습니다.

## 핵심 변경
- `CorrectionStore.list_filtered()`를 추가해 `original_text`/`corrected_text` query 검색, status 필터, query+status AND 조건, 최신순 limit을 지원했습니다.
- `SQLiteCorrectionStore.list_filtered()`를 추가했습니다. 실제 SQLite schema에는 `original_text`/`corrected_text` 컬럼이 없고 `data` JSON에 저장되므로 `json_extract(data, ...)` 기반 SQL WHERE로 구현했습니다.
- `get_correction_list(query, status, limit)`가 `list_filtered()`를 사용하고, active preference fingerprint와 겹치는 correction에 `has_active_preference`를 붙이도록 했습니다.
- `/api/corrections/list` GET 라우트에서 `query`와 `status` query parameter를 읽어 service로 전달하도록 했습니다.
- frontend client에 `fetchCorrectionList(params)`와 `has_active_preference` 타입을 추가하고, `PreferencePanel` 최근 교정 섹션에 검색 input 및 `[충돌]` 배지를 추가했습니다.
- JSON/SQLite store 단위 테스트에 query 검색, status 필터, query+status AND, 빈 결과 케이스를 추가했습니다.

## 검증
- `sha256sum .pipeline/implement_handoff.md` → `daaf80e66754c53b3f7b93b73d22f83ebc7fac3dd06bab2712ba21216087c523` 일치
- `app/frontend/node_modules/.bin/tsc --noEmit --project app/frontend/tsconfig.json` → PASS
- `python3 -m py_compile storage/correction_store.py storage/sqlite_store.py app/handlers/aggregate.py app/web.py` → PASS
- `python3 -m unittest -v tests.test_correction_store` → PASS, 35 tests
- `python3 -m unittest -v tests.test_sqlite_store` → PASS, 39 tests
- `git diff --check -- storage/correction_store.py storage/sqlite_store.py app/handlers/aggregate.py app/web.py app/frontend/src/api/client.ts app/frontend/src/components/PreferencePanel.tsx tests/test_correction_store.py tests/test_sqlite_store.py` → PASS
- 추가 확인: `python3 -m unittest -v tests.test_correction_summary` → PASS, 4 tests

## 남은 리스크
- handoff의 시작 브랜치 `feat/m69-axis1-correction-search-conflict` 생성은 `.git/refs` 쓰기 제한으로 실패했습니다. 현재 브랜치는 `feat/m68-promote-pattern`이며 변경은 작업트리에만 남아 있습니다.
- `origin/main`은 로컬에서 M68 merge를 반영하지 않은 상태로 보였고, 이번 변경은 현재 M68 HEAD 위에 적용했습니다.
- dist 재빌드는 handoff 경계상 M69 Axis 2 담당이라 수행하지 않았습니다.
- commit, push, PR 생성은 수행하지 않았습니다.
