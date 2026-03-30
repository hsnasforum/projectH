# 2026-03-27 historical_save_identity_signal 구현

## 변경 파일
- `app/web.py`
- `tests/test_web_app.py`
- `docs/PRODUCT_SPEC.md`
- `docs/ARCHITECTURE.md`
- `docs/ACCEPTANCE_CRITERIA.md`
- `docs/MILESTONES.md`
- `docs/TASK_BACKLOG.md`
- `docs/NEXT_STEPS.md`
- `plandoc/2026-03-27-save-axis-adjunct-contract.md`
- `work/3/27/2026-03-27-historical-save-identity-signal-implementation.md`

## 사용 skill
- `approval-flow-audit`: save approval identity replay가 current `save_signal`을 덮어쓰지 않고 approval-gated save contract를 유지하는지 점검했습니다.
- `security-gate`: task-log를 canonical current-state source로 승격하지 않고 helper-only audit replay로 제한했는지 확인했습니다.
- `doc-sync`: shipped helper와 first-slice `write_note`-only replay 규칙에 맞춰 spec / architecture / acceptance / roadmap / plandoc 문구를 동기화했습니다.
- `release-check`: py_compile, focused unittest, diff cleanliness, 관련 키워드 검색 결과만 실제 실행 기준으로 정리했습니다.
- `work-log-closeout`: 이번 라운드 closeout을 저장소 형식으로 남겼습니다.

## 변경 이유
- 직전 closeout 기준으로 content-side `superseded_reject_signal`은 해결됐지만, save-axis에서는 later explicit action 뒤 `save_signal.latest_approval_id`가 떨어질 수 있었습니다.
- save happened 사실 자체는 current `save_signal`에 남아도 approval-backed save identity가 사라질 수 있어서, current-state signal을 건드리지 않는 좁은 historical adjunct가 필요했습니다.

## 핵심 변경
- `app/web.py` session serialization에 source-message-anchored optional `historical_save_identity_signal`을 추가했습니다.
- helper는 same-anchor task-log의 `write_note`에서 non-empty `approval_id`가 있는 approval-backed persisted save만 읽어, 최신 historical save identity 하나만 replay하도록 고정했습니다.
- current `save_signal`이 여전히 `latest_approval_id`를 갖고 있으면 helper를 suppress 하고, current save linkage와 replay candidate의 `save_content_source` / `saved_note_path`가 어긋나면 omit 하도록 좁게 처리했습니다.
- `approval_granted`만 있는 경우 helper를 만들지 않는 회귀 테스트를 추가해 first slice가 granted-but-not-written approval state를 replay하지 않도록 고정했습니다.
- 문서는 shipped `historical_save_identity_signal`, `write_note`-only replay 규칙, 그리고 남은 open question이 later `approval_granted` corroboration 여부라는 점으로 갱신했습니다.

## 검증
- `python3 -m py_compile storage/session_store.py app/web.py core/agent_loop.py tests/test_smoke.py tests/test_web_app.py`
- `python3 -m unittest -v tests.test_smoke tests.test_web_app`
  - `Ran 152 tests in 1.689s`
  - `OK`
- `git diff --check`
- `rg -n "historical_save_identity_signal|save_signal|latest_approval_id|save_content_source|saved_note_path|approval_id|write_note|approval_granted" storage/session_store.py app/web.py core/agent_loop.py tests/test_smoke.py tests/test_web_app.py docs/PRODUCT_SPEC.md docs/ARCHITECTURE.md docs/ACCEPTANCE_CRITERIA.md docs/MILESTONES.md docs/TASK_BACKLOG.md docs/NEXT_STEPS.md`

## 남은 리스크
- 이전 closeout에서 남아 있던 save-axis `latest_approval_id` loss 자체는 이번 라운드에서 해소했지만, first slice는 same-anchor `write_note` audit만 사용하므로 later `approval_granted` corroboration이 필요한지 여부는 별도 open question으로 남습니다.
- helper는 at-most-one latest historical approval-backed save identity만 replay하므로, broader save history viewer나 cross-artifact aggregate는 여전히 future scope입니다.
