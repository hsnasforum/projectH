# 2026-04-30 M118 publish bundle (docs_sync 수정 인라인 + commit)

## 변경 파일

### Commit 1 — `99d35a6` (13개)
- `storage/session_store.py`
- `storage/sqlite/session.py`
- `storage/preference_utils.py`
- `tests/test_session_store.py`
- `tests/test_sqlite_store.py`
- `tests/test_preference_handler.py`
- `docs/PRODUCT_SPEC.md`
- `docs/ACCEPTANCE_CRITERIA.md`
- `docs/ARCHITECTURE.md`
- `docs/MILESTONES.md`
- `docs/TASK_BACKLOG.md`
- `docs/NEXT_STEPS.md` ← 사전 기존 docs_sync 수정 (126→127)
- `README.md` ← 사전 기존 docs_sync 수정 (entry #127 추가)

- `work/4/30/2026-04-30-m118-publish-bundle.md`

## 실행 내용

- `operator_request.md` CONTROL_SEQ 1532 (`commit_push_bundle_authorization + pr_creation_gate`) 처리 (operator_retriage 인라인).
- 사전 기존 `test_docs_sync` 실패 수정:
  - `docs/NEXT_STEPS.md` smoke count 126 → 127
  - `README.md` entry #127 추가 (M113 review-queue 액션 인라인 이동)
- `python3 -m unittest tests.test_docs_sync.BrowserSmokeInventoryDocsParityTest` — 3 tests PASS (수정 후).
- 신규 브랜치 `feat/m118-injected-count-api-exposure` (base: `feat/m117-injection-feedback-loop`) 생성.

## 결과

| 항목 | 결과 |
|------|------|
| Commit SHA | `99d35a6` — feat(preferences): expose injected_count in preferences API and fix aggregation (M118) |
| 브랜치 | `feat/m118-injected-count-api-exposure` |
| push | ✓ `origin/feat/m118-injected-count-api-exposure` |
| PR 생성 | ✓ [#112](https://github.com/hsnasforum/projectH/pull/112) — draft, base: `feat/m117-injection-feedback-loop` |
| 변경 통계 | 13 files changed, 81 insertions(+), 17 deletions(-) |

## 스태킹 링크

PR #91–#111 ← #112 (`feat/m118-injected-count-api-exposure`) — 모두 draft.

## 남은 리스크

- PR #91–#112 모두 draft, `pr_merge_gate` operator 대기
- M118 Axis 2 (frontend TypeScript 타입 + PreferencePanel UI + dist rebuild + E2E) 미완
- M118 advisory의 "Display 'Injected {N} times ({M}% applied)'" UI는 Axis 2 보류
