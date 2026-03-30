# 2026-03-27 corrected-save long history smoke

## 변경 파일
- `e2e/tests/web-smoke.spec.mjs`
- `tests/test_web_app.py`
- `README.md`
- `docs/PRODUCT_SPEC.md`
- `docs/ARCHITECTURE.md`
- `docs/ACCEPTANCE_CRITERIA.md`
- `docs/MILESTONES.md`
- `docs/TASK_BACKLOG.md`
- `docs/NEXT_STEPS.md`
- `e2e/README.md`

## 사용 skill
- `e2e-smoke-triage`: corrected-save 저장 뒤 late reject / re-correct chain을 기존 Playwright fixture 패턴에 맞춰 가장 작은 시나리오로 고정했습니다.
- `approval-flow-audit`: corrected-save saved snapshot, later reject, later correction이 approval semantics를 바꾸지 않는지 점검했습니다.
- `doc-sync`: smoke count와 long-history scenario 설명을 README, acceptance, milestone, backlog, next-step, spec, architecture, e2e README에 맞췄습니다.
- `release-check`: 실제 실행한 py_compile, focused unittest, Playwright smoke, rg 점검, diff hygiene만 closeout에 반영했습니다.
- `work-log-closeout`: 이번 라운드 변경과 검증, 남은 리스크를 표준 섹션으로 정리했습니다.

## 변경 이유
- 직전 closeout에서 남은 핵심 리스크는 corrected-save로 실제 저장한 뒤 늦게 `내용 거절`을 기록하고, 다시 `수정본 기록`으로 latest state를 바꾸는 더 긴 history chain이 아직 browser baseline으로 고정되지 않았다는 점이었습니다.
- 이번 라운드 목표는 현재 shipped corrected-save / reject-note semantics는 그대로 둔 채, saved corrected snapshot history와 latest verdict, latest corrected state가 서로 다른 층으로 움직인다는 점을 Playwright와 focused regression으로 고정하는 것이었습니다.

## 핵심 변경
- Playwright smoke에 `corrected-save 저장 뒤 늦게 내용 거절하고 다시 수정해도 saved snapshot과 latest state가 분리됩니다` 시나리오를 추가했습니다.
- 새 scenario는 corrected-save 승인 저장 -> late reject -> reject note update -> later correction submit까지 한 경로에서 아래를 함께 확인합니다.
  - saved corrected snapshot note/body/path는 그대로 유지됨
  - latest content verdict는 `rejected`로 바뀔 수 있음
  - later correction submit은 다시 latest corrected state를 `corrected`로 이동시키고 stale reject note를 숨김
  - 어느 단계도 저장된 corrected snapshot body를 자동으로 덮어쓰지 않음
- focused service regression 1개를 추가했습니다.
  - corrected-save 완료 뒤 late reject와 reject note를 거친 다음, later correction submit이 source message의 latest state를 `corrected`로 복원하고 stale `content_reason_record`를 지우는 반면, saved corrected snapshot history와 실제 note 파일은 그대로 남는지 확인합니다.
- 앱 코드는 이번 라운드에서 수정하지 않았습니다.
  - 기존 quick meta, saved-result wording, correction/content-verdict state만으로 long-history chain을 충분히 안정적으로 읽을 수 있음을 확인했습니다.
- smoke 문서는 실제 기준 10개 시나리오로 동기화했고, corrected-save long-history chain 설명을 관련 문서에 반영했습니다.

## 검증
- `python3 -m py_compile app/web.py tests/test_smoke.py tests/test_web_app.py`
- `python3 -m unittest -v tests.test_smoke tests.test_web_app`
  - `Ran 146 tests in 2.034s`
  - `OK`
- `make e2e-test`
  - `10 passed (1.6m)`
- `rg -n "corrected-save|내용 거절|거절 메모 기록|rejected|content_reason_record|latest verdict|저장했습니다|수정본 기록" e2e/tests/web-smoke.spec.mjs app/templates/index.html app/web.py tests/test_smoke.py tests/test_web_app.py README.md docs/ACCEPTANCE_CRITERIA.md docs/MILESTONES.md docs/TASK_BACKLOG.md docs/NEXT_STEPS.md e2e/README.md docs/PRODUCT_SPEC.md docs/ARCHITECTURE.md`
- `git diff --check`

## 남은 리스크
- 이전 closeout에서 이어받은 “corrected-save 저장 이후 late reject / re-correct long history chain 미고정” 리스크는 이번 라운드에서 해소했습니다.
- 이번 라운드에서 의도적으로 범위 밖에 둔 사항은 manual blank-note clear UX, richer reject labels, approval semantics 확장입니다.
- 여전히 남은 리스크는 corrected-save 저장 이후 다시 late reject / re-correct / re-save가 여러 번 반복되는 더 긴 반복 history chain을 별도 browser scenario로 얼마나 더 쪼갤지입니다.
