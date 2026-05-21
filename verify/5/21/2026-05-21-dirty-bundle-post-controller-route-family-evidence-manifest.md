# 2026-05-21 dirty bundle post controller route family evidence manifest 검증

## 검증 대상
- `work/5/21/2026-05-21-dirty-bundle-post-controller-route-family-evidence-manifest.md`
- `verify/5/21/2026-05-21-controller-route-family-local-evidence-aggregate.md`
- `.pipeline/implement_handoff.md#2071`

## 변경 파일
- 없음
- 이 검증 단계는 코드, 테스트, 제품 문서, `/work`를 수정하지 않았고 이 `/verify` 기록만 추가했다.

## 사용 skill
- `round-handoff`: 최신 `/work` manifest를 직전 `/verify` 및 좁은 diff/markdown evidence와 대조하고 다음 control 전 `/verify`를 남기는 데 사용했다.
- `next-slice-triage`: 검증 truth가 현재화된 뒤 implement/advisory/operator 후보를 좁히는 데 사용했다.

## 실행한 확인
- `sed -n '1,260p' work/5/21/2026-05-21-dirty-bundle-post-controller-route-family-evidence-manifest.md`
  - 통과. 최신 `/work`는 변경 파일이 해당 `/work` manifest뿐인 evidence-only 기록이며, production code/test/docs, `/verify`, advisory/operator control을 수정하지 않았다고 기록한다.
- `sed -n '1,240p' verify/5/21/2026-05-21-controller-route-family-local-evidence-aggregate.md`
  - 통과. 직전 `/verify`가 controller route-family aggregate evidence를 확인했고, 다음 local slice로 dirty-bundle evidence manifest를 선택했음을 확인했다.
- `git diff --check -- work/5/21/2026-05-21-dirty-bundle-post-controller-route-family-evidence-manifest.md verify/5/21/2026-05-21-controller-route-family-local-evidence-aggregate.md .pipeline/implement_handoff.md`
  - 통과.
- `git diff --check --no-index -- /dev/null work/5/21/2026-05-21-dirty-bundle-post-controller-route-family-evidence-manifest.md`
  - whitespace 오류 없음. 파일이 untracked라 diff 존재로 종료코드 1이 반환되지만 출력은 없었다.
- `git status --short -- work/5/21/2026-05-21-dirty-bundle-post-controller-route-family-evidence-manifest.md verify/5/21/2026-05-21-controller-route-family-local-evidence-aggregate.md .pipeline/implement_handoff.md .pipeline/advisory_request.md .pipeline/operator_request.md controller/server.py tests/test_controller_server.py README.md docs/ARCHITECTURE.md docs/ACCEPTANCE_CRITERIA.md docs/PRODUCT_SPEC.md`
  - 확인. `controller/server.py`, `tests/test_controller_server.py`, `README.md`, `docs/ARCHITECTURE.md`, `docs/ACCEPTANCE_CRITERIA.md`, `docs/PRODUCT_SPEC.md`는 여전히 dirty이고, 최신 `/work`와 직전 `/verify` 파일은 untracked 상태다. `.pipeline/advisory_request.md` / `.pipeline/operator_request.md`는 아직 없었다.
- `git status --short | awk '{counts[substr($0,1,2)]++} END {for (k in counts) print k, counts[k]}'`
  - 확인. 검증 시점에는 ` M 35`, `?? 93`이었다. 최신 `/work` 작성 뒤 새 work note가 추가되었기 때문에 `/work`에 기록된 `?? 92`보다 하나 늘어난 상태로 판단했다.
- `git ls-files --others --exclude-standard | wc -l`
  - 확인. 검증 시점에는 untracked 파일 수가 `237`이었다. 최신 `/work` 작성 뒤 새 work note가 추가되었기 때문에 `/work`에 기록된 `236`보다 하나 늘어난 상태로 판단했다.
- `git diff --stat -- controller/server.py tests/test_controller_server.py README.md docs/ARCHITECTURE.md docs/ACCEPTANCE_CRITERIA.md docs/PRODUCT_SPEC.md work/5/20/ verify/5/20/ verify/5/21/ work/5/21/2026-05-21-dirty-bundle-post-controller-route-family-evidence-manifest.md`
  - 통과. tracked dirty stat은 여전히 6개 tracked file 기준 `720 insertions(+)`, `49 deletions(-)`로 최신 `/work`와 일치한다.

## 판단
- 최신 `/work`의 핵심 주장은 현재 파일 상태와 모순되지 않는다. 해당 라운드는 dirty-bundle local evidence와 held gate를 기록한 evidence-only manifest였고, code/test/docs 변경이나 publication 작업은 없었다.
- 최신 `/work`의 count evidence는 manifest 작성 시점의 값이며, 현재 검증 시점에서 untracked count가 하나 증가한 것은 그 manifest 파일 자체가 추가된 결과로 해석된다.
- 최신 controller route-family evidence는 직전 `/work`의 socket-free compile/unit aggregate 기록에 의존하며, 이번 verify prompt의 `SCOPE_HINT`가 변경 파일 기준 markdown truth 우선 확인을 지시했으므로 unit/Playwright를 다시 실행하지 않았다.
- `RUNTIME_STATUS_AT_DISPATCH`는 `runtime_state: RUNNING`, `automation_health: recovering`, `automation_next_action: retrying`이므로 runtime liveness 판단에는 이 dispatcher surface를 authoritative로 사용했다. lane-local `status --json`, `doctor --json`, `tmux` 검사는 실행하지 않았다.

## 실행하지 않은 확인
- `python3 -m py_compile`, `python3 -m unittest`, Playwright, full controller smoke, broad e2e, long soak, socket-bound HTTP, runtime start/stop 검사는 실행하지 않았다.
- 이유: 최신 `/work`의 변경 파일은 `/work` manifest뿐이고, 검증 지시가 code/test/runtime 변경이 없으면 unit 또는 Playwright로 넓히지 말라고 제한했다.

## 남은 확인과 위험
- dirty bundle은 여전히 크다. 검증 시점 기준 tracked modified 35개 항목, untracked status 항목 93개, untracked 파일 237개가 남아 있다.
- browser/socket/live-runtime/release/publication gate는 계속 held다.
- controller-smoke pass, full-smoke pass, release-ready, publication-approved 상태는 주장하지 않는다.
- 같은 evidence-only manifest를 더 이어가는 것은 current-risk reduction이 낮다. 다음 blocking boundary는 이 dirty bundle을 계속 local-only로 둘지, operator가 별도 publication flow를 명시적으로 승인할지에 대한 operator-only 결정이다.

## 다음 control 판단
- `COUNCIL_DECISION: operator_required`
- `REASON_CODE: dirty_bundle_publication_or_hold_decision`
- `OWNER_ROLE: operator`
- `NEXT_CONTROL_FILE: .pipeline/operator_request.md`
- `NEXT_CONTROL_SEQ: 2072`
- `EVIDENCE: work/5/21/2026-05-21-dirty-bundle-post-controller-route-family-evidence-manifest.md`
- `EVIDENCE: verify/5/21/2026-05-21-dirty-bundle-post-controller-route-family-evidence-manifest.md`
- `EVIDENCE: verify/5/21/2026-05-21-controller-route-family-local-evidence-aggregate.md`
- `REJECTED: implement_handoff for commit/push/PR` - implement prompts forbid commit, push, branch/PR publication, merge, and release work.
- `REJECTED: another evidence-only manifest` - 최신 dirty-bundle manifest already captures local evidence and held gates; repeating the same local manifest would create a low-value loop.
- `REJECTED: advisory_request` - `ADVISORY_ENABLED: false`.
