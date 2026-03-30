## 변경 파일
- `core/approval.py`
- `core/agent_loop.py`
- `storage/session_store.py`
- `app/web.py`
- `tests/test_smoke.py`
- `tests/test_web_app.py`
- `README.md`
- `docs/PRODUCT_SPEC.md`
- `docs/ARCHITECTURE.md`
- `docs/ACCEPTANCE_CRITERIA.md`
- `docs/MILESTONES.md`
- `docs/TASK_BACKLOG.md`
- `docs/NEXT_STEPS.md`

## 사용 skill
- `approval-flow-audit`
- `security-gate`
- `doc-sync`
- `release-check`
- `work-log-closeout`

## 변경 이유
- 직전 closeout에서 이어받은 핵심 리스크는 corrected text와 future save approval가 나중에 만날 때, 현재 original-draft save path의 trace shape가 다시 흔들릴 수 있다는 점이었습니다.
- 이번 라운드에서는 corrected-save approval UI나 action을 미리 만들지 않고, 현재 shipped original-draft save flow에만 explicit save-target discriminator를 넣어 미래 확장을 위한 내부 기반을 먼저 고정해야 했습니다.
- 승인 기반 저장과 corrected text artifact를 계속 분리하면서도, 나중 corrected-save approval가 같은 trace contract를 재사용할 수 있어야 했습니다.

## 핵심 변경
- `save_content_source`를 current save-target discriminator field name으로 고정했습니다.
- 현재 truthful 값은 `original_draft` 하나만 허용했습니다.
- save-note approval object, pending approval serialization, approval-related response payload, direct approved save response, save-related session message, approval/write task-log detail에 같은 field를 추가했습니다.
- legacy pending save approval load에서도 `save_content_source`가 없으면 `original_draft`로 backfill되도록 정규화해서 backward compatibility를 유지했습니다.
- original grounded-brief content source-of-truth는 그대로 두고, 이 field는 approval/write trace contract 쪽에만 추가했습니다.
- direct approved save는 approval object가 없으므로 saved response와 saved source message에만 same field를 노출했습니다.

## 검증
- 실행:
  - `python3 -m py_compile core/approval.py core/agent_loop.py app/web.py storage/session_store.py storage/task_log.py tests/test_smoke.py tests/test_web_app.py`
  - `python3 -m unittest -v tests.test_smoke tests.test_web_app`
  - `git diff --check`
  - `rg -n "save_content_source|original_draft" core/approval.py core/agent_loop.py app/web.py storage/session_store.py storage/task_log.py tests/test_smoke.py tests/test_web_app.py docs/PRODUCT_SPEC.md docs/ARCHITECTURE.md docs/ACCEPTANCE_CRITERIA.md docs/MILESTONES.md docs/TASK_BACKLOG.md docs/NEXT_STEPS.md README.md`
- 미실행:
  - `python3 -m unittest -v`
  - `make e2e-test`

## 남은 리스크
- 이전 closeout에서 남아 있던 “corrected text를 나중에 어떤 명시 action으로 save target으로 올릴지” 리스크는 아직 남아 있습니다.
- 이번 라운드에서 해소한 리스크는 current original-draft save path가 future corrected-save approval와 다른 trace shape를 쓰게 되는 위험입니다.
- 여전히 남은 리스크는 future corrected-save approval가 들어올 때:
  - 어떤 explicit bridge action으로 approval preview를 새로 만들지
  - `save_content_source = corrected_text`일 때 approval preview body와 write body를 어떤 snapshot으로 고정할지
  - current direct-approved save path와 later corrected-save path를 UI copy상 어떻게 덜 헷갈리게 분리할지
