# 2026-04-17 docs: pipeline-runtime adoption/cutover verification-default cleanup (seq 281)

## 변경 파일

- `docs/projectH_pipeline_runtime_docs/00_문서세트_안내.md`
- `docs/projectH_pipeline_runtime_docs/01_개발계획서.md`
- `docs/projectH_pipeline_runtime_docs/02_요구사항_명세서.md`
- `docs/projectH_pipeline_runtime_docs/04_QA_시험계획서.md`
- `docs/projectH_pipeline_runtime_docs/07_마이그레이션_체크리스트.md`

## 사용 skill

- 없음

## 변경 이유

- `docs/TASK_BACKLOG.md:153-155`와 `docs/projectH_pipeline_runtime_docs/05_운영_RUNBOOK.md §3.5 현재 검증 원칙`은 이미 day-to-day 기본 검증을 `launcher live stability gate + incident replay + 실제 작업 세션` 3축으로 고정했지만, 같은 runtime 문서 세트의 00/01/02/04/07 문서는 여전히 6h/24h soak 중심 표현이 남아 기본 검증처럼 읽힐 수 있었습니다.
- `.pipeline/claude_handoff.md` seq 281은 "Docs pipeline-runtime-docs adoption/cutover verification-default cleanup" 한 슬라이스로 이 잔여 drift를 닫도록 지시했습니다.
- Gemini advisory seq 279가 `2026-04-09` response-payload docs family는 이미 닫혔다고 확정했고, 남은 작업은 `docs/TASK_BACKLOG.md:155`의 adoption/cutover docs 잔여 정리였습니다.

## 핵심 변경

- 5개 문서 모두에 RUNBOOK §3.5를 day-to-day 검증 authority로 명시하는 framing note를 추가하고, 6h/24h soak 표현을 "historical baseline / 채택(adoption)·cutover gate" 문맥으로 재배치했습니다.
- `00_문서세트_안내.md`: §1에 "본 문서 세트의 6h/24h soak은 채택·cutover baseline 전용이며 기본 검증이 아니다" 참고 블록 추가, §3 문서 설명에서 04는 adoption/baseline 기준임을 명시하고 05에 "현재 검증 원칙 (§3.5)"을 authority로 덧붙임.
- `01_개발계획서.md`: §2.4 "24시간 soak의 위치" 신설로 본 계획서의 24h/6h soak 표현이 채택/cutover baseline gate임을 고정, §4.1 최종 목표와 §5 Phase 7 Internal tooling adoption gate, §6 Must 리스트, §10 승인 게이트 문구를 "1회 채택 baseline / 이후 day-to-day는 RUNBOOK §3.5 3축"으로 정리.
- `02_요구사항_명세서.md`: NFR-001 제목과 본문을 "24시간 안정성 (채택 baseline)" + "day-to-day authority = RUNBOOK §3.5"로 재구성하고 수용 기준에 "채택 baseline 1회 수행 기준"과 적용 범위 메모 추가, 이해관계자 표의 QA 항목도 같은 framing으로 조정.
- `04_QA_시험계획서.md`: §1 QA 목표 상단에 "이 문서의 soak는 채택/baseline gate용, 기본 검증은 RUNBOOK §3.5" 참고 블록 추가, §3.4 Soak Test와 §6 24시간 Soak Test 설계 제목에 "(채택/baseline 전용)" 명시, §6.2 권장 실행 경로에 "day-to-day는 이 명령 대신 RUNBOOK §3.5 3축" 라인 추가, §7 Internal tooling adoption gate 도입문, §10 QA 종료 기준 도입문, §11 결론을 모두 채택/cutover 주기 문맥으로 재작성.
- `07_마이그레이션_체크리스트.md`: §2 전환 원칙 뒤에 "본 체크리스트의 6h/24h soak = 채택/cutover baseline" 참고 블록 추가, §4 Stage G 목표/체크 항목을 "채택 baseline 1회"로 표시하고 "채택 이후 day-to-day는 RUNBOOK §3.5 3축" 확인 항목 추가, §7 cutover 종료 선언 조건에도 같은 운영 문서 명시 항목 추가.
- `05_운영_RUNBOOK.md`는 이미 authority 문구가 있어 이번 슬라이스에서 수정하지 않았습니다(핸드오프 scope 유지).

## 검증

- `git diff --check -- docs/projectH_pipeline_runtime_docs/00_문서세트_안내.md docs/projectH_pipeline_runtime_docs/01_개발계획서.md docs/projectH_pipeline_runtime_docs/02_요구사항_명세서.md docs/projectH_pipeline_runtime_docs/04_QA_시험계획서.md docs/projectH_pipeline_runtime_docs/07_마이그레이션_체크리스트.md`: whitespace/conflict marker 없음.
- `docs/TASK_BACKLOG.md:153-155`, `docs/projectH_pipeline_runtime_docs/05_운영_RUNBOOK.md:65-115`를 직접 재확인해 현재 검증 원칙 3축 / synthetic soak의 보조 게이트 포지션이 authority로 유지됨을 확인했고, 5개 문서가 이 truth와 모순되지 않도록 정렬했습니다.
- `rg -n "24h soak|24시간 soak|6h mini soak|기본 검증|일상 운영 절차|adoption gate|baseline" docs/projectH_pipeline_runtime_docs/00_문서세트_안내.md docs/projectH_pipeline_runtime_docs/01_개발계획서.md docs/projectH_pipeline_runtime_docs/02_요구사항_명세서.md docs/projectH_pipeline_runtime_docs/04_QA_시험계획서.md docs/projectH_pipeline_runtime_docs/07_마이그레이션_체크리스트.md`: 매칭 라인 모두 채택/baseline/adoption·cutover gate 또는 RUNBOOK §3.5 authority를 명시하는 맥락 안에 있음을 확인했습니다.
- 코드/테스트/런처/워처/런타임/컨트롤러 edit 없음 → 이번 슬라이스는 docs-only이므로 Python 또는 Playwright suite는 재실행하지 않았습니다.

## 남은 리스크

- 이번 변경은 5개 문서 범위로 제한되었고, `05_운영_RUNBOOK.md`(이미 authority), `03_기술설계_명세서.md`(이번 슬라이스 비대상), `06_ADR_아키텍처_결정기록.md`는 건드리지 않았습니다. 만약 후속 라운드에서 03/06 쪽에도 같은 default-gate drift가 남아 있으면 별도 작은 docs 슬라이스로 한 번 더 정리해야 합니다.
- 작업 시작 시점부터 `.pipeline/current_run.json`, `.pipeline/runs/...`, `watcher_core.py`, `watcher_prompt_assembly.py`, `docs/.../03_기술설계_명세서.md`, `docs/.../05_운영_RUNBOOK.md`가 이미 dirty 상태였고 handoff 지시에 따라 이번 라운드에서 revert/normalize하지 않았습니다. 이 unrelated dirty state는 이번 closeout 책임 밖입니다.
- 이번 handoff seq 281은 `docs/TASK_BACKLOG.md:155` "adoption/cutover docs cleanup 잔여"를 닫는 것이며, `2026-04-09` current-message docs family는 Gemini advisory seq 279 및 앞선 verify 결과대로 이미 닫힌 상태이므로 이번 변경으로 재개되지 않습니다.
