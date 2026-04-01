# 2026-03-31 latest-update noisy history-card reload lock verification

## 변경 파일
- `verify/3/31/2026-03-31-latest-update-noisy-history-card-reload-lock-verification.md`
- `.pipeline/codex_feedback.md`

## 사용 skill
- `round-handoff`
- `investigation-quality-audit`

## 변경 이유
- 사용자 요청에 따라 `AGENTS.md`, `work/README.md`, `verify/README.md`, `.pipeline/README.md`를 먼저 읽고, latest Claude `/work`인 `work/3/31/2026-03-31-latest-update-noisy-history-card-reload-lock.md`와 같은 날 latest `/verify`인 `verify/3/31/2026-03-31-latest-update-noisy-source-filtering-verification.md`를 기준으로 이번 라운드 주장만 좁게 검수해야 했습니다.
- latest `/work`는 same-family `B: latest_update answer-mode noise filtering`에서 history-card `load_web_search_record_id` reload 경로의 noisy role/URL 미노출 regression 1건을 test-only로 잠갔다고 적고 있으므로, 이번 검수에서는 그 테스트가 실제로 추가되었는지, 검증 자기보고가 맞는지, 그리고 그 closeout이 family closure까지 truthfully 말했는지만 확인하면 충분했습니다.

## 핵심 변경
- 판정: latest `/work`의 핵심 변경 주장은 대부분 사실입니다. [`tests/test_web_app.py`](/home/xpdlqj/code/projectH/tests/test_web_app.py#L9618) 에 `test_handle_chat_latest_update_noisy_source_excluded_after_history_card_reload`가 실제로 추가되어 있고, `load_web_search_record_id` reload 경로에서 `answer_mode == "latest_update"`, noisy role `보조 커뮤니티` 미노출, noisy URL `brunch` 미노출을 잠급니다.
- `/work`의 `production 코드 변경 없음` 주장도 이번 round-local 범위에서는 사실입니다. `stat` 기준 [`core/agent_loop.py`](/home/xpdlqj/code/projectH/core/agent_loop.py#L5054) mtime은 `2026-03-31 21:36:47`로, 이전 verify/handoff보다 앞서 있고 이번 `/work`와 새 테스트 파일보다 이릅니다. 이번 라운드에서 새로 움직인 파일은 사실상 [`tests/test_web_app.py`](/home/xpdlqj/code/projectH/tests/test_web_app.py#L9618) 뿐이었습니다.
- `/work`의 검증 자기보고도 사실입니다. `python3 -m unittest -v tests.test_web_app`를 다시 돌려 `Ran 126 tests in 2.734s`, `OK`를 확인했고, `git diff --check -- core/agent_loop.py tests/test_web_app.py`도 통과했습니다.
- 범위도 current `projectH` 방향을 벗어나지 않았습니다. 이번 변경은 document-first MVP 안의 secondary web investigation regression test 1건 추가에 머물렀고, ranking rewrite, docs sync, approval flow, browser-visible UI 확장은 섞이지 않았습니다.
- 다만 latest `/work`의 "`latest_update noisy source filtering family`는 닫힘" 주장은 아직 사실이 아닙니다. 수동 fixture replay로 `뉴스 1건 + noisy community 1건` latest_update를 재현해 보니, 첫 응답과 저장된 history badge는 `verification_label == "단일 출처 참고"`로 맞지만, 같은 record를 `load_web_search_record_id`로 다시 불러오면 [`response_origin.verification_label`](/home/xpdlqj/code/projectH/core/agent_loop.py#L5086) 이 `다중 출처 참고`로 다시 올라갑니다. 즉 noisy source는 `source_roles`와 본문에서는 숨겨졌지만, 같은 history-card reload 경로에서 badge semantics는 아직 single-source truth를 과장합니다.
- 따라서 이번 라운드는 test 추가 자체는 truthful하게 완료되었지만, family closure까지는 truthfully 닫지 못했습니다. whole-project audit 사안은 아니므로 `report/`는 만들지 않았습니다.

## 검증
- `python3 -m unittest -v tests.test_web_app`
  - 통과 (`Ran 126 tests in 2.734s`, `OK`)
- `git diff --check -- core/agent_loop.py tests/test_web_app.py`
  - 통과 (출력 없음)
- 수동 truth 대조
  - `work/3/31/2026-03-31-latest-update-noisy-history-card-reload-lock.md`
  - `verify/3/31/2026-03-31-latest-update-noisy-source-filtering-verification.md`
  - `.pipeline/codex_feedback.md`
  - `tests/test_web_app.py`
  - `core/agent_loop.py`
- 추가 수동 재현
  - `_FakeWebSearchTool`로 `뉴스 1건 + noisy community 1건` latest_update fixture 구성
  - 첫 응답 `response_origin.verification_label == "단일 출처 참고"`
  - `session.web_search_history[0].verification_label == "단일 출처 참고"`
  - 같은 record를 `load_web_search_record_id`로 reload하면 `response_origin.verification_label == "다중 출처 참고"`

## 남은 리스크
- latest `/work`가 잠근 noisy role/URL 미노출 regression 자체는 맞습니다.
- 하지만 같은 history-card reload 경로에서 `verification_label`이 noisy source를 이유로 single-source truth를 `다중 출처 참고`로 과장하므로, `B: latest_update answer-mode noise filtering` family는 아직 닫히지 않았습니다.
- 다음 라운드는 새 축이 아니라, 같은 family의 가장 작은 current-risk로 `latest_update noisy history-card reload verification_label parity`만 잠그는 편이 맞습니다.
