# 2026-04-22 second pass trusted priority

## 변경 파일
- `core/agent_loop.py`
- `tests/test_smoke.py`
- `work/4/22/2026-04-22-second-pass-trusted-priority.md`

## 사용 skill
- `investigation-quality-audit`: entity-card second-pass reinvestigation 정렬이 conflict와 untrusted-only weak slot을 더 먼저 재조사하도록 좁게 확인했습니다.
- `security-gate`: web investigation 변경이 read-only search 흐름의 권한 게이트, 로컬 기록, 저장/write 경계를 바꾸지 않는지 확인했습니다.
- `finalize-lite`: 구현 종료 전 필수 검증과 문서 동기화 필요성을 점검했습니다.
- `work-log-closeout`: 실제 변경 파일, 실행 명령, 남은 리스크 기준으로 이 closeout을 작성했습니다.

## 변경 이유
- `.pipeline/implement_handoff.md` CONTROL_SEQ 762의 exact slice에 따라 `_build_entity_second_pass_queries()`가 `CoverageStatus.CONFLICT`와 `trusted_source_count == 0` weak slot을 기존 non-missing weak slot보다 먼저 재조사하도록 했습니다.
- Milestone 4의 "reinvestigate weak or unresolved slots more effectively" 범위에서 새 status 값이나 UI/저장 스키마 확장 없이 second-pass query 우선순위만 조정했습니다.

## 핵심 변경
- `pending_slots.sort(...)`를 `_pending_slot_sort_key()`로 바꿔 tier 계산을 명시했습니다.
- `CONFLICT` slot을 최우선 tier로 두어 일반 weak slot보다 먼저 probe query가 생성되게 했습니다.
- `trusted_source_count == 0`인 non-missing/non-conflict slot을 양수 trusted source count를 가진 weak slot보다 먼저 두었습니다.
- 기존 missing slot 내부 순서(`prior_probe_count >= 1` missing이 일반 missing보다 먼저)를 유지했습니다.
- `tests/test_smoke.py`에 conflict slot 우선순위와 zero-trusted weak slot 우선순위를 검증하는 회귀 테스트 2개를 추가했습니다.

## 검증
- `python3 -m py_compile core/agent_loop.py` 통과
- `python3 -m unittest tests.test_smoke` 통과 (`146 tests`)
- `git diff --check` 통과

## 남은 리스크
- 이번 라운드는 commit/push/PR을 수행하지 않았습니다.
- 이번 handoff 범위 밖의 기존 dirty tree가 남아 있습니다: `app/frontend/src/components/MessageBubble.tsx`, `app/frontend/src/types.ts`, `app/serializers.py`, `core/web_claims.py`, `docs/ARCHITECTURE.md`, `docs/PRODUCT_SPEC.md`, 이전 `/work`, `/verify`, `report/gemini` 파일 등입니다.
- 이번 변경은 second-pass query ordering만 조정했으며, Playwright/browser-visible 검증은 요구 범위가 아니라 실행하지 않았습니다.
