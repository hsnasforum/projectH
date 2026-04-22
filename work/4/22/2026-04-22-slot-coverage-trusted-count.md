# 2026-04-22 slot coverage trusted count

## 변경 파일
- `core/web_claims.py`
- `tests/test_smoke.py`
- `work/4/22/2026-04-22-slot-coverage-trusted-count.md`

## 사용 skill
- `investigation-quality-audit`: claim coverage의 weak/strong 구분 보강이 조사 품질 불확실성 표시에 미치는 영향을 확인했습니다.
- `security-gate`: web investigation 관련 변경이 읽기 전용/권한 게이트/감사 경계를 바꾸지 않는지 확인했습니다.
- `finalize-lite`: 구현 종료 전 필수 검증, 문서 동기화 필요성, `/work` closeout 준비 상태를 좁게 확인했습니다.
- `work-log-closeout`: 실제 변경 파일, 실행 명령, 남은 리스크 기준으로 이 closeout을 작성했습니다.

## 변경 이유
- `.pipeline/implement_handoff.md` CONTROL_SEQ 756의 exact slice에 따라 `CoverageStatus.WEAK` 안에서 신뢰 출처가 1개 있는 경우와 비신뢰 출처만 있는 경우를 구분할 수 있는 내부 필드를 추가했습니다.
- Milestone 4의 "strong facts, weak facts, unresolved slots" 분리 강화 범위 안에서 새 status 값이나 UI/저장 스키마 확장 없이 현재 claim coverage 판단 정보를 보강했습니다.

## 핵심 변경
- `SlotCoverage`에 additive 필드 `trusted_source_count: int = 0`을 추가했습니다.
- `summarize_slot_coverage()`에서 missing slot은 `trusted_source_count=0`, non-missing slot은 기존 `_trusted_supporting_source_count(primary)` 결과를 저장하도록 했습니다.
- strong 판정에서도 같은 `trusted_count` 값을 재사용해 신뢰 출처 수 계산 로직을 중복하지 않았습니다.
- `tests/test_smoke.py`에 비신뢰 출처만 있는 weak slot의 `trusted_source_count=0`, 공식 단일 출처 weak slot의 양수 count, strong slot의 trusted support count 회귀 검사를 추가했습니다.
- UI, approval flow, 저장 세션/search record shape, pipeline control slot은 변경하지 않았습니다.

## 검증
- `python3 -m py_compile core/web_claims.py core/contracts.py` 통과
- `python3 -m unittest tests.test_smoke` 통과 (`144 tests`)
- `git diff --check` 통과

## 남은 리스크
- 이번 라운드는 commit/push/PR을 수행하지 않았습니다.
- `trusted_source_count`는 현재 `SlotCoverage` 내부 필드이며, 브라우저 claim coverage payload나 표시 문구로 노출하는 작업은 별도 slice입니다.
- 문서 동기화는 수행하지 않았습니다. 이번 변경은 새 UI 동작, 저장 스키마, approval 계약, roadmap 상태 변경을 만들지 않았습니다.
