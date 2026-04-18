# 2026-04-17 entity-card trusted-agreement conflict-sensitive claim coverage verification

## 변경 파일
- `verify/4/17/2026-04-17-entity-card-trusted-agreement-conflict-sensitive-claim-coverage-verification.md`
- `.pipeline/gemini_request.md`

## 사용 skill
- `round-handoff`

## 변경 이유
- `work/4/17/2026-04-17-entity-card-trusted-agreement-conflict-sensitive-claim-coverage.md`가 entity-card claim synthesis의 `[교차 확인]` 기준을 더 엄격하게 바꿨다고 기록했으므로, 실제 구현/문서/검증이 현재 트리와 맞는지 다시 확인해야 했습니다.
- 같은 날짜 최신 `/verify`는 `verify/4/17/2026-04-17-entity-card-reinvestigation-top3-ranking-verification.md`였고, 이번 `/work`에 대응하는 verification note는 아직 없었습니다.
- 특히 `/work` 검증 섹션이 focused regression뿐 아니라 `python3 -m unittest tests.test_web_app` 전체 통과까지 적고 있어, 그 줄이 현재 verify 환경에서도 재현되는지 분리해서 확인할 필요가 있었습니다.

## 핵심 변경
- `/work`가 설명한 구현 자체는 현재 트리와 맞습니다. `core/web_claims.py`에는 `_trusted_supporting_source_count()`와 `_has_competing_trusted_alternative()`가 실제로 추가되어 있고, `summarize_slot_coverage()`는 이제 `primary.support_count >= 2`, `trusted supporting source >= 2`, `competing trusted alternative 없음`을 모두 만족할 때만 `CoverageStatus.STRONG`으로 남습니다.
- `/work`가 말한 focused regression도 실제 파일에 존재합니다. `tests/test_smoke.py`에는 untrusted-only agreement가 `strong`이 되지 않아야 하는 케이스와 conflicting trusted alternative가 `weak`로 내려가야 하는 케이스가 추가되어 있습니다.
- `docs/PRODUCT_SPEC.md`의 entity-card agreement-over-noise 문장은 현재 구현과 맞게 갱신되어 있습니다. `docs/ACCEPTANCE_CRITERIA.md`는 browser-visible literal label 계약을 계속 설명하고 있고, 이번 trusted-agreement semantic change를 별도 truth-sync해야 하는 직접 drift는 찾지 못했습니다.
- focused rerun 기준으로는 `/work`의 핵심 주장이 현재도 성립합니다. `py_compile`, `tests.test_smoke -k summarize_slot_coverage`, `claim_coverage`, `entity`, `reinvestigation`, `tests.test_web_app -k claim_coverage`, `entity`, `reinvestigation`, 그리고 `tests.test_smoke` 전체가 모두 통과했습니다.
- 다만 `/work`의 마지막 전체-suite 줄은 현재 verify 환경에서 재현되지 않았습니다. `python3 -m unittest tests.test_web_app`는 `Ran 310 tests in 163.778s` 뒤에 `FAILED (errors=10)`으로 끝났고, 실패는 모두 `LocalOnlyHTTPServer(("127.0.0.1", 0), service)`를 여는 handler tests에서 `PermissionError: [Errno 1] Operation not permitted`가 난 케이스였습니다 (`app/web.py:246`). 이 실패군은 이번 entity-card 변경 파일과는 직접 관련이 없지만, `/work`의 `Ran 310 tests, OK` 문장을 현재 truth로 유지할 수는 없습니다.
- 다음 exact slice는 아직 저신뢰입니다. browser-investigation family 안에서 남은 후보가 여러 개라 이번 round의 next control은 speculative `STATUS: implement`보다 `Gemini` arbitration이 맞습니다.

## 검증
- `python3 -m py_compile core/web_claims.py tests/test_smoke.py tests/test_web_app.py`
  - 결과: 통과
- `python3 -m unittest tests.test_smoke -k summarize_slot_coverage`
  - 결과: `Ran 2 tests`, `OK`
- `python3 -m unittest tests.test_smoke -k claim_coverage`
  - 결과: `Ran 5 tests`, `OK`
- `python3 -m unittest tests.test_smoke -k entity`
  - 결과: `Ran 21 tests`, `OK`
- `python3 -m unittest tests.test_smoke -k reinvestigation`
  - 결과: `Ran 3 tests`, `OK`
- `python3 -m unittest tests.test_web_app -k claim_coverage`
  - 결과: `Ran 21 tests`, `OK`
- `python3 -m unittest tests.test_web_app -k entity`
  - 결과: `Ran 55 tests`, `OK`
- `python3 -m unittest tests.test_web_app -k reinvestigation`
  - 결과: `Ran 3 tests`, `OK`
- `git diff --check -- core/web_claims.py tests/test_smoke.py tests/test_web_app.py docs/PRODUCT_SPEC.md docs/ACCEPTANCE_CRITERIA.md`
  - 결과: 출력 없음
- `rg -n "교차 확인|설명형 다중 출처 합의|설명형 단일 출처|agreement-over-noise|trusted agreement|strong" docs/ACCEPTANCE_CRITERIA.md`
  - 결과: 기존 browser-visible label/count-summary 계약만 확인했고, 이번 trusted-agreement semantic change를 별도 설명해야 하는 직접 drift는 찾지 못했습니다.
- `python3 -m unittest tests.test_smoke`
  - 결과: `Ran 113 tests`, `OK`
- `python3 -m unittest tests.test_web_app`
  - 결과: `Ran 310 tests in 163.778s`, `FAILED (errors=10)`
  - 실패군: `tests.test_web_app.WebAppServiceTest`의 handler tests 10건
  - 공통 오류: `LocalOnlyHTTPServer(("127.0.0.1", 0), service)` 생성 시 `PermissionError: [Errno 1] Operation not permitted`
- Playwright / `make e2e-test`
  - 미실행. 이번 변경은 `core/web_claims.py`의 backend 판정 규칙과 그에 묶인 Python regression 범위였고, browser selector/layout/copy를 직접 바꾸지 않았습니다.

## 남은 리스크
- 현재 verify 환경에서는 `tests.test_web_app` 전체 suite가 handler socket bind permission 문제로 닫히지 않습니다. 이번 entity-card 슬라이스의 focused regressions는 통과했지만, 이후 `/work`에서 whole-suite `OK`를 적으려면 이 family를 실제로 재현 가능한 환경에서 다시 확인해야 합니다.
- 다음 exact browser-investigation slice는 아직 저신뢰입니다. verification label wording 정합화, history/meta count-summary coherence, 추가 synthesis weighting 중 하나가 다른 후보를 명확히 이긴다고 보기 어려워 `Gemini` arbitration을 다시 열었습니다.
- 더티 worktree(`controller/js/sidebar.js`, `core/agent_loop.py`, runtime docs bundle, `e2e/tests/controller-smoke.spec.mjs`, `verify/4/9/...`, `controller/test.html`, 기존 `report/gemini/...`, `work/4/17/...`, `verify/4/17/...`)는 이번 verify round와 무관한 항목까지 섞여 있으므로 그대로 두었습니다.
