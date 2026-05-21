# 2026-05-21 dirty bundle post controller route family evidence manifest

## 변경 파일
- `work/5/21/2026-05-21-dirty-bundle-post-controller-route-family-evidence-manifest.md`

## 사용 skill
- `work-log-closeout`: evidence-only implement 라운드의 실제 상태 증거, 실행 명령, held gate, 남은 리스크를 한국어 `/work` manifest로 남기기 위해 사용했다.

## 변경 이유
- `.pipeline/implement_handoff.md#2071`가 controller route-family aggregate evidence 이후 현재 dirty bundle의 local evidence와 held gate를 한 번에 갱신하라고 지시했다.
- `work/5/20/2026-05-20-controller-route-family-local-evidence-aggregate.md`는 controller route-family 누적 변경에 대해 `python3 -m py_compile controller/server.py tests/test_controller_server.py`, `python3 -m unittest -v tests.test_controller_server`, `git diff --check ...` 통과를 기록했다.
- `verify/5/21/2026-05-21-controller-route-family-local-evidence-aggregate.md`는 해당 `/work`가 evidence-only closeout이며, code/test/runtime 변경이 없었기 때문에 unit/Playwright를 다시 돌리지 않았다고 검증했다.
- 이번 라운드는 publication이 아니라 dirty bundle의 최신 local evidence와 아직 held인 gate를 명확히 기록하는 manifest slice다.

## 핵심 변경
- production code, tests, product docs, `/verify`, `.pipeline/advisory_request.md`, `.pipeline/operator_request.md`는 수정하지 않았다.
- 현재 tracked dirty shape는 `git status --short` 기준 modified 35개 항목이다.
- 현재 untracked shape는 `git status --short` 기준 92개 항목이고, `git ls-files --others --exclude-standard | wc -l` 기준 untracked 파일 236개다.
- 지정된 dirty-bundle evidence path의 diff stat은 `README.md`, `controller/server.py`, `docs/ACCEPTANCE_CRITERIA.md`, `docs/ARCHITECTURE.md`, `docs/PRODUCT_SPEC.md`, `tests/test_controller_server.py` 6개 파일 기준 `720 insertions(+)`, `49 deletions(-)`다.
- 대표 untracked evidence에는 `.pipeline/freeze-snapshots/`, `controller/js/queue-presentation.js`, `pipeline_runtime/state_contract.py`, `tests/fixtures/`, `tests/test_controller_queue_presentation.py`, `tests/test_pipeline_runtime_state_contract.py`, 다수의 `work/` 및 `verify/` 기록이 포함된다.
- commit, push, branch/PR publication, merge, release는 수행하지 않았다.

## 검증
- `sha256sum .pipeline/implement_handoff.md`
  - 통과. handoff SHA가 `88d1d86b704c40443b76e6cedde67c9ec70cf66cdb9fa0e4efaef434567c9ff0`와 일치했다.
- `ls -lt work/5/21 | head -20`
  - 통과. manifest 작성 전 `work/5/21/`에는 기존 work note가 없었다.
- `test -e work/5/21/2026-05-21-dirty-bundle-post-controller-route-family-evidence-manifest.md; echo $?`
  - 통과. 작성 전 대상 manifest가 없었고 결과는 `1`이었다.
- `git status --short`
  - 통과. 전체 dirty bundle의 tracked/untracked 상태를 확인했다.
- `git diff --stat -- controller/server.py tests/test_controller_server.py README.md docs/ARCHITECTURE.md docs/ACCEPTANCE_CRITERIA.md docs/PRODUCT_SPEC.md work/5/20/ verify/5/20/ verify/5/21/`
  - 통과. 위 6개 tracked file 기준 `720 insertions(+)`, `49 deletions(-)`를 확인했다.
- `git diff --check -- controller/server.py tests/test_controller_server.py README.md docs/ARCHITECTURE.md docs/ACCEPTANCE_CRITERIA.md docs/PRODUCT_SPEC.md work/5/20/ verify/5/20/ verify/5/21/`
  - 통과.
- `git diff --name-only`
  - 통과. tracked modified path 목록을 확인했다.
- `git ls-files --others --exclude-standard | wc -l`
  - 통과. untracked 파일 수 `236`을 확인했다.
- `git ls-files --others --exclude-standard | sed -n '1,80p'`
  - 통과. 대표 untracked path를 확인했다.
- `git status --short | awk '{counts[substr($0,1,2)]++} END {for (k in counts) print k, counts[k]}'`
  - 통과. ` M 35`, `?? 92`를 확인했다.
- `git diff --check --no-index -- /dev/null work/5/21/2026-05-21-dirty-bundle-post-controller-route-family-evidence-manifest.md`
  - whitespace 오류 없음. 새 work note가 untracked라 diff 존재로 종료코드 1이 반환되지만 출력은 없었다.
- `git diff --check -- controller/server.py tests/test_controller_server.py README.md docs/ARCHITECTURE.md docs/ACCEPTANCE_CRITERIA.md docs/PRODUCT_SPEC.md work/5/20/ verify/5/20/ verify/5/21/ work/5/21/2026-05-21-dirty-bundle-post-controller-route-family-evidence-manifest.md`
  - 통과.
- `git status --short -- work/5/21/2026-05-21-dirty-bundle-post-controller-route-family-evidence-manifest.md .pipeline/advisory_request.md .pipeline/operator_request.md controller/server.py tests/test_controller_server.py README.md docs/ARCHITECTURE.md docs/ACCEPTANCE_CRITERIA.md docs/PRODUCT_SPEC.md`
  - 통과. 새 work note가 untracked이고, `.pipeline/advisory_request.md` / `.pipeline/operator_request.md`는 없음을 확인했다.
- `test ! -e .pipeline/advisory_request.md && test ! -e .pipeline/operator_request.md`
  - 통과.

## 남은 리스크
- 이번 라운드는 evidence-only manifest 작성에 한정했다. `python3 -m py_compile`, `python3 -m unittest`, Playwright, full controller smoke, broad e2e, long soak, socket-bound HTTP, runtime start/stop, `status --json`, `doctor --json`, `tmux` liveness checks는 실행하지 않았다.
- 최신 controller route-family evidence는 직전 `/work`의 socket-free compile/unit aggregate 기록에 의존한다. 이번 manifest 라운드에서 그 unit checks를 새로 실행하지 않았다.
- browser/socket/live-runtime/release/publication gate는 계속 held다.
- dirty bundle은 여전히 크며, release readiness, full-smoke pass, controller-smoke pass, publication approval을 주장하지 않는다.
- 이 manifest는 publication 승인이나 PR 준비 완료 신호가 아니라, 현재 local evidence와 held gate를 명시한 운영 기록이다.
