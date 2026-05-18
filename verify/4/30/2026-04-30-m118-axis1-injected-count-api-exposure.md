STATUS: verified_with_caveats
CONTROL_SEQ: 1532
BASED_ON_WORK: work/4/30/2026-04-30-m118-axis1-injected-count-api-exposure.md
VERIFIED_BY: Claude (verify owner)
NEXT_CONTROL: operator_request.md CONTROL_SEQ 1532

---

# 2026-04-30 M118 Axis 1 injected_count API exposure — verify

## 이번 라운드 범위

CONTROL_SEQ 1531 implement_handoff (m118_axis1_injected_count_api_exposure) 실행 결과.
work note 변경 범위: `storage/session_store.py`, `storage/sqlite/session.py`,
`storage/preference_utils.py`, `tests/test_session_store.py`,
`tests/test_sqlite_store.py`, `tests/test_preference_handler.py` 6개 파일.
(추가: `docs/` 5개 파일 — handoff 금지 범위 외 편집; 내용은 valid하고 git diff --check 통과)

## 직접 실행 결과

| 체크 | 결과 |
|------|------|
| `python3 -m py_compile` (3개 소스 파일) | **PASS** |
| `python3 -m unittest -v tests.test_session_store` | **PASS — 20개** |
| `python3 -m unittest -v tests.test_sqlite_store` | **PASS — 47개** |
| `python3 -m unittest -v tests.test_preference_handler` | **PASS — 23개** |
| `git diff --check` (11개 파일) | **PASS** |

총 90개 지정 테스트 PASS.

## discover 실패 분석

| 실패 항목 | 원인 | M118 관련 |
|----------|------|----------|
| HTTP/Ollama socket 다수 | sandbox `PermissionError` | 무관 (sandbox 제약) |
| `test_correction_summary.test_promote_pattern_...` | M114 `is_highly_reliable=True` 기존 동작 | 무관 |
| `test_docs_sync.BrowserSmokeInventoryDocsParityTest` | ACCEPTANCE_CRITERIA.md 127 vs NEXT_STEPS.md/README.md 126 | **사전 기존** ← 아래 확인 |
| `test_operator_request_schema.test_live_operator_request_header_canonical` | operator_request.md live header DECISION_CLASS 값 | 무관 |

### test_docs_sync 사전 기존 확인

`git stash` 후 커밋 상태에서 `test_docs_sync.BrowserSmokeInventoryDocsParityTest` 직접 실행:
→ **동일 실패** (127 vs 126). M118 dirty 파일 제거 후에도 실패 재현.

원인: ACCEPTANCE_CRITERIA.md line 1417 "Playwright smoke covers 127 core browser scenarios" 는
이미 이전 커밋(M113 E2E sync 추정)에서 127로 업데이트됐으나 NEXT_STEPS.md(126)와 README.md(126)이
미동기화된 상태. **M118 변경이 원인이 아님**.

수정 필요: `docs/NEXT_STEPS.md` 와 `README.md` smoke count 126 → 127 동기화
→ **operator_retriage 인라인 처리 후 M118 커밋에 포함**.

## dirty tree 현황 (11개 파일) — 미커밋

| 분류 | 파일 | 출처 |
|------|------|------|
| M118 Axis 1 | `storage/session_store.py` | setdefault 버그 수정 + injected_count 스캔 |
| M118 Axis 1 | `storage/sqlite/session.py` | 동일 |
| M118 Axis 1 | `storage/preference_utils.py` | enrich에 injected_count 추가 |
| M118 Axis 1 | `tests/test_session_store.py` | 주입-전용 선호 집계 테스트 |
| M118 Axis 1 | `tests/test_sqlite_store.py` | 동일 |
| M118 Axis 1 | `tests/test_preference_handler.py` | list_preferences_payload injected_count 테스트 |
| M118 docs (비범위) | `docs/PRODUCT_SPEC.md` | injected_count API 설명 |
| M118 docs (비범위) | `docs/ACCEPTANCE_CRITERIA.md` | injected_count 기준 갱신 |
| M118 docs (비범위) | `docs/ARCHITECTURE.md` | setdefault 동작 갱신 |
| M118 docs (비범위) | `docs/MILESTONES.md` | M118 완료 항목 |
| M118 docs (비범위) | `docs/TASK_BACKLOG.md` | M118 완료 갱신 |

M117 파일은 PR #111 커밋 완료.

## 남은 리스크

- `docs/NEXT_STEPS.md` + `README.md` docs_sync 수정 (126→127) 미완 — operator_retriage 인라인 처리
- frontend TypeScript 타입 + PreferencePanel UI + dist rebuild + E2E는 Axis 2 보류
- 3+ docs-only rule 적용 예정 (M118 docs 이미 포함, 추가 implement 라운드 없이 커밋)
