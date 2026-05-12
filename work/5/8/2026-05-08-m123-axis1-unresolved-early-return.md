# 2026-05-08 M123 Axis 1 UNRESOLVED early-return 억제

## 변경 파일

- `core/agent_loop.py`
- `tests/test_smoke.py`
- `work/5/8/2026-05-08-m123-axis1-unresolved-early-return.md`

## 사용 skill

- `investigation-quality-audit`: entity-card second-pass query behavior 변경이 UNRESOLVED 불확실성을 숨기지 않는지 점검했다.
- `finalize-lite`: 구현 후 검증, 문서 동기화 필요성, closeout 준비 상태를 핸드오프 범위 안에서 확인했다.
- `work-log-closeout`: 변경 파일, 실행 검증, 남은 리스크를 표준 `/work` 형식으로 정리했다.

## 변경 이유

M122 Axis 2에서 `CoverageStatus.UNRESOLVED`가 추가됐지만,
`_build_entity_second_pass_queries()`의 이른 반환 조건은 STRONG 슬롯 수와 핵심 슬롯 충족 여부만 확인했다.
그 결과 STRONG 슬롯이 충분하면 UNRESOLVED 슬롯이 남아 있어도 second-pass 보강 쿼리를 건너뛸 수 있었다.

## 핵심 변경

- `core/agent_loop.py`에서 `_build_entity_second_pass_queries()`가 `unresolved_slots`를 계산하도록 했다.
- 기존 STRONG 슬롯 충분 조건에 `and not unresolved_slots`를 추가해 UNRESOLVED 슬롯이 남아 있으면 이른 반환하지 않게 했다.
- `tests/test_smoke.py`에 UNRESOLVED 슬롯이 남은 경우 second-pass 쿼리가 생성되는 회귀 테스트를 추가했다.
- STRONG 슬롯만 충분한 기존 완료 케이스는 계속 빈 리스트를 반환하는 회귀 테스트를 추가했다.
- entity-card second-pass 경로만 변경했으며 latest-update, UI, E2E, `.pipeline`은 수정하지 않았다.

## 검증

- PASS: `python3 -m py_compile core/agent_loop.py`
- PASS: `python3 -m unittest -v tests.test_smoke.SmokeTest.test_second_pass_does_not_early_return_when_unresolved_slot_remains tests.test_smoke.SmokeTest.test_second_pass_keeps_early_return_when_strong_slots_are_sufficient`
- PASS: `python3 -m unittest -v tests.test_smoke` — 158 tests
- PASS: `git diff --check -- core/agent_loop.py tests/test_smoke.py`
- PASS: `git diff --check -- core/agent_loop.py tests/test_smoke.py work/5/8/2026-05-08-m123-axis1-unresolved-early-return.md`

## 남은 리스크

- 문서 파일은 핸드오프 금지 범위라 수정하지 않았다. 이번 변경은 사용자 표시 문구나 UI 계약 변경이 아니라 entity-card 보강 쿼리 조건의 내부 품질 보정으로 판단했다.
- 브라우저/UI/E2E는 변경 범위가 아니어서 실행하지 않았다.
- commit, push, PR 생성은 수행하지 않았다.
