# 2026-04-01 mdilbo latest-work truth-sync stop

## 변경 파일
- `verify/4/1/2026-04-01-mdilbo-latest-work-truth-sync-stop.md`
- `.pipeline/codex_feedback.md`

## 사용 skill
- `round-handoff`

## 변경 이유
- 사용자 요청에 따라 `AGENTS.md`, `work/README.md`, `verify/README.md`, `.pipeline/README.md`를 먼저 다시 읽고 검수를 시작했습니다.
- 오늘(`2026-04-01`) 새 `/work`가 없어서 규칙대로 전날 최신 Claude `/work`인 `work/3/31/2026-03-31-mdilbo-news-domain-coverage.md`를 기준으로 잡았고, 같은 날 최신 `/verify`는 `verify/3/31/2026-03-31-mdilbo-news-domain-coverage-verification.md`였습니다.
- 이번 요청의 1차 목적은 latest `/work`가 여전히 truthful한지 다시 확인하는 것이었지만, 재대조 중 current code/test truth가 그 canonical pair보다 앞서 나가 있어 automation handoff를 계속 `STATUS: implement`로 두면 거짓 handoff가 된다는 점을 확인했습니다.

## 핵심 변경
- latest `/work`의 mdilbo 라운드 주장은 현재 코드 기준으로는 여전히 사실입니다. `core/source_policy.py`와 `core/agent_loop.py`에는 `mdilbo.com`이 들어 있고, `tests/test_source_policy.py`와 `tests/test_web_app.py`의 `mdilbo` assertion/regression도 그대로 존재합니다.
- 다만 current code/test truth는 latest `/work`와 latest `/verify`보다 한 슬라이스 더 앞서 있습니다. `core/source_policy.py`, `core/agent_loop.py`, `tests/test_source_policy.py`, `tests/test_web_app.py`에는 이미 `idaebae.com` news-domain hint, source-policy assertion, `test_handle_chat_latest_update_idaebae_mk_noisy_community_badge_contract`가 추가되어 있습니다.
- 수동 확인에서도 `classify_source_type('https://www.idaebae.com/news/articleView.html?idxno=123456') -> news`가 나왔습니다. 이는 current `.pipeline/codex_feedback.md`가 아직 “`idaebae.com`을 구현하라”는 `STATUS: implement` handoff를 유지하는 것과 모순됩니다. 해당 handoff는 이미 구현된 slice를 다시 구현하라고 지시하는 stale handoff입니다.
- 파일 수정 시각도 이 drift를 뒷받침합니다. `core/source_policy.py`, `core/agent_loop.py`, `tests/test_source_policy.py`, `tests/test_web_app.py`의 수정 시각은 latest `/verify`인 `verify/3/31/2026-03-31-mdilbo-news-domain-coverage-verification.md`보다 뒤입니다. 즉 latest `/verify` 이후 코드/테스트가 더 바뀌었는데, 그 변경을 설명하는 새 `/work` closeout은 아직 없습니다.
- 범위 자체가 현재 `projectH` 방향을 벗어난 것은 아닙니다. drift는 여전히 secondary web investigation의 같은 `latest_update news-domain coverage` family 안에 머물러 있고, product surface나 approval/document workflow를 넓히지는 않았습니다.
- docs 무변경 자체는 현재도 사실입니다. `README.md`, `docs/PRODUCT_SPEC.md`, `docs/ACCEPTANCE_CRITERIA.md`, `docs/MILESTONES.md`, `docs/TASK_BACKLOG.md`, `docs/NEXT_STEPS.md`는 모두 latest `/work`보다 새롭지 않고, `mdilbo`, `무등일보`, `idaebae`, `대구신문` 언급도 없습니다. 다만 canonical persistent truth는 `/work`와 `/verify`가 맡아야 하므로, 이번 문제의 핵심은 문서 누락이 아니라 최신 구현 closeout 부재입니다.
- 따라서 이번 round의 정직한 결론은 “계획된 다음 slice가 이미 코드에 들어가 있어 latest `/work` / `/verify` / `.pipeline` truth가 어긋났다”입니다. 이 상태에서는 다음 구현 slice를 자동 확정하면 안 되므로 `.pipeline/codex_feedback.md`를 `STATUS: needs_operator`로 내려야 합니다.
- whole-project audit이 필요한 징후는 없어 `report/`는 만들지 않았습니다. 이번 이슈는 narrow truth-sync stop입니다.

## 검증
- `python3 -m unittest -v tests.test_source_policy tests.test_web_app`
  - 통과 (`Ran 161 tests in 3.211s`, `OK`)
- `git diff --check -- core/source_policy.py core/agent_loop.py tests/test_source_policy.py tests/test_web_app.py`
  - 통과 (출력 없음)
- 수동 truth 대조
  - `work/3/31/2026-03-31-mdilbo-news-domain-coverage.md`
  - `verify/3/31/2026-03-31-mdilbo-news-domain-coverage-verification.md`
  - `.pipeline/codex_feedback.md`
  - `core/source_policy.py`
  - `core/agent_loop.py`
  - `tests/test_source_policy.py`
  - `tests/test_web_app.py`
  - `README.md`
  - `docs/PRODUCT_SPEC.md`
  - `docs/ACCEPTANCE_CRITERIA.md`
  - `docs/MILESTONES.md`
  - `docs/TASK_BACKLOG.md`
  - `docs/NEXT_STEPS.md`
- 추가 수동 확인
  - `classify_source_type('https://www.mdilbo.com/detail/c3QycN/740000') -> news`
  - `classify_source_type('https://www.idaebae.com/news/articleView.html?idxno=123456') -> news`
  - `rg -n "mdilbo|idaebae|test_handle_chat_latest_update_mdilbo|test_handle_chat_latest_update_idaebae" ...`로 mdilbo와 idaebae 구현/테스트가 모두 현재 코드에 들어 있음을 확인
  - `README.md`, `docs/PRODUCT_SPEC.md`, `docs/ACCEPTANCE_CRITERIA.md`, `docs/MILESTONES.md`, `docs/TASK_BACKLOG.md`, `docs/NEXT_STEPS.md`에서 `mdilbo|무등일보|idaebae|대구신문` 검색 결과 없음
  - latest `/verify` 이후 수정 시각 재확인 결과 `core/source_policy.py`, `core/agent_loop.py`, `tests/test_source_policy.py`, `tests/test_web_app.py`가 latest `/verify`보다 늦게 갱신됨을 확인

## 남은 리스크
- current code에는 `idaebae.com` slice가 이미 들어가 있지만 이를 설명하는 새 `/work` closeout이 없습니다. canonical truth가 끊긴 상태라 다음 구현 slice를 자동 확정하면 handoff가 거짓이 됩니다.
- operator는 post-verify `idaebae.com` 변경이 의도된 Claude 작업인지 먼저 판단해야 합니다. 의도된 작업이면 Claude가 새 기능을 더 구현하기 전에 그 이미-적용된 slice에 대한 truthful `/work` closeout을 먼저 남기게 해야 합니다.
- 의도되지 않은 변경이면 code/work/pipeline truth를 먼저 복구해야 합니다. 어느 경우든, 지금은 `STATUS: implement`를 유지하면 안 됩니다.
