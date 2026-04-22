# 2026-04-22 claim coverage trusted count exposure

## 변경 파일
- `core/agent_loop.py`
- `app/serializers.py`
- `app/frontend/src/types.ts`
- `app/frontend/src/components/MessageBubble.tsx`
- `tests/test_smoke.py`
- `docs/PRODUCT_SPEC.md`
- `docs/ARCHITECTURE.md`
- `work/4/22/2026-04-22-claim-coverage-trusted-count-exposure.md`

## 사용 skill
- `investigation-quality-audit`: claim coverage의 weak slot 표시가 신뢰 출처 유무를 과장하지 않는지 확인했습니다.
- `e2e-smoke-triage`: browser-visible claim coverage badge 변경에 대해 지정된 Playwright slice를 먼저 시도하고 실패 원인을 분리했습니다.
- `security-gate`: web investigation 변경이 읽기 전용/권한 게이트/로컬 기록 경계를 바꾸지 않는지 확인했습니다.
- `doc-sync`: serialized `claim_coverage` slot object shape 변경을 제품/아키텍처 문서에 좁게 반영했습니다.
- `finalize-lite`: 구현 종료 전 실행한 검증과 미실행/실패 검증을 분리해 정리했습니다.
- `work-log-closeout`: 실제 변경 파일, 실행 명령, 남은 리스크 기준으로 이 closeout을 작성했습니다.

## 변경 이유
- `.pipeline/implement_handoff.md` CONTROL_SEQ 759의 exact slice에 따라 CONTROL_SEQ 756에서 추가된 `SlotCoverage.trusted_source_count`를 claim-coverage payload와 React badge 렌더링까지 전달했습니다.
- 같은 `WEAK` 상태라도 신뢰 출처가 1개 이상인 약한 사실과 비신뢰 출처만 있는 noise를 UI badge에서 구분할 수 있게 했습니다.

## 핵심 변경
- `_build_entity_claim_coverage_items()`가 missing/non-missing slot 모두에 `trusted_source_count`를 포함하도록 했고, legacy `SlotCoverage`에는 `getattr(..., 0)` 기본값을 유지했습니다.
- `_serialize_claim_coverage()`가 `trusted_source_count`를 정수 기본값 `0`으로 통과시키도록 했습니다.
- `ClaimCoverageItem` 타입에 optional `trusted_source_count?: number`를 추가했습니다.
- `MessageBubble`의 claim coverage badge가 `WEAK && trusted_source_count > 0`일 때만 amber `?`를 표시하고, `trusted_source_count == 0`인 weak는 stone `-`로 표시하도록 했습니다.
- `tests/test_smoke.py`의 기존 claim coverage 내부 필드/serializer 테스트가 `trusted_source_count` 전달을 함께 고정하도록 보강했습니다.
- `docs/PRODUCT_SPEC.md`, `docs/ARCHITECTURE.md`의 `claim_coverage` slot object shape에 `trusted_source_count`, `support_plurality`, `trust_tier`를 명시했습니다.

## 검증
- `python3 -m py_compile core/agent_loop.py app/serializers.py` 통과
- `python3 -m unittest tests.test_smoke` 통과 (`144 tests`)
- `git diff --check` 통과
- `cd e2e && npx playwright test tests/web-smoke.spec.mjs -g "claim-coverage" --reporter=line` 실패: Playwright webServer가 `python3 -m app.web` 시작 중 소켓 생성에서 `PermissionError: [Errno 1] Operation not permitted`로 종료되어 시나리오 실행 전 중단됨
- 추가 확인: `cd app/frontend && npx tsc --noEmit` 실패. 이번 변경 파일이 아니라 기존 `src/components/Sidebar.tsx`의 SVG `title` prop, `src/hooks/useChat.ts`의 `applied_preferences` 타입, `src/main.tsx`의 `./index.css` declaration 오류에서 중단됨

## 남은 리스크
- 이번 라운드는 commit/push/PR을 수행하지 않았습니다.
- Playwright claim-coverage slice는 현재 sandbox에서 local app server socket 생성이 막혀 완료하지 못했습니다. 소켓 바인딩이 허용되는 환경에서 같은 명령 재실행이 필요합니다.
- frontend 전체 TypeScript no-emit 검사는 기존 오류로 실패했습니다. 이번 `trusted_source_count` 타입 추가 자체는 오류 목록에 나타나지 않았습니다.
- 현재 dirty tree에는 이전 라운드의 `core/web_claims.py`, 기존 `/work` closeout, verify/report 파일도 함께 남아 있습니다. 커밋 전 포함 범위를 다시 확인해야 합니다.
