# 2026-03-27 corrected-save helper and snapshot wording

## 변경 파일
- `app/templates/index.html`
- `core/agent_loop.py`
- `tests/test_smoke.py`
- `tests/test_web_app.py`
- `README.md`
- `docs/PRODUCT_SPEC.md`
- `docs/ARCHITECTURE.md`
- `docs/ACCEPTANCE_CRITERIA.md`
- `docs/MILESTONES.md`
- `docs/TASK_BACKLOG.md`
- `docs/NEXT_STEPS.md`
- `plandoc/2026-03-27-corrected-save-bridge-and-snapshot-contract.md`
- `work/3/27/2026-03-27-corrected-save-helper-and-snapshot-wording.md`

## 사용 skill
- `frontend-skill`: correction area와 approval helper copy를 작업용 UI 톤으로 짧고 명확하게 정리하는 데 사용했습니다.
- `approval-flow-audit`: corrected-save bridge action, approval card, save-result wording을 다루면서 approval-gated write와 immutable snapshot 불변식을 다시 확인했습니다.
- `security-gate`: corrected-save wording 변경이 승인 기반 저장 계약을 넓히지 않는지 점검했습니다.
- `doc-sync`: 구현된 helper/snapshot wording을 README와 제품 문서, backlog/next-step 문구에 동기화했습니다.
- `release-check`: 실제 실행한 정적 확인, focused unittest, diff hygiene만 closeout에 반영했습니다.
- `work-log-closeout`: 이번 라운드 closeout을 표준 섹션으로 정리했습니다.

## 변경 이유
- 직전 closeout에서 이어받은 첫 번째 리스크는 corrected-save bridge action을 correction area에 항상 보일지, recorded correction이 있을 때만 보일지 정책이 아직 고정되지 않았다는 점이었습니다.
- 두 번째 리스크는 source message의 최신 `corrected_text`와 이미 열린 corrected-save approval snapshot 또는 이미 저장된 corrected-save body가 달라질 수 있는데, 현재 UI/문구가 그 차이를 충분히 정직하게 드러내지 못한다는 점이었습니다.
- 이번 라운드에서는 corrected-save bridge semantics, original-draft save path, immutable snapshot 계약은 그대로 유지한 채, always-visible disabled-helper policy와 snapshot wording만 additive하게 정리해야 했습니다.

## 핵심 변경
- correction area에서 `이 수정본으로 저장 요청` 버튼을 항상 보이게 유지하고, recorded `corrected_text`가 없으면 disabled 상태와 helper copy로 먼저 `수정본 기록`이 필요하다는 점을 명확히 드러냈습니다.
- recorded correction이 있는 상태에서 textarea가 기록본과 같을 때와, textarea가 다시 dirty 상태가 되었을 때를 분리해 상태 문구를 바꿨습니다.
- dirty 상태에서는 bridge action이 여전히 마지막 recorded correction만 사용하고, 현재 입력 중인 변경을 저장 대상으로 올리려면 다시 `수정본 기록`을 눌러야 한다는 점을 correction area에서 직접 설명하도록 했습니다.
- approval 카드 메타 문구에 corrected-save approval preview가 요청 시점에 고정된 스냅샷이며, 나중에 수정본을 다시 기록해도 자동으로 바뀌지 않고 더 새 수정본을 저장하려면 새 bridge action이 필요하다는 점을 추가했습니다.
- corrected-save approval 응답과 corrected-save save-result 응답 문구를 request-time snapshot 기준으로 더 정직하게 바꿨고, response/transcript quick meta에도 `저장 기준 요청 시점 수정본 스냅샷` 라벨을 추가했습니다.
- focused regression으로 template source copy, corrected-save bridge response wording, corrected-save save-result wording을 함께 검증하고 관련 문서를 동기화했습니다.

## 검증
- 실행:
  - `python3 -m py_compile app/web.py core/agent_loop.py tests/test_smoke.py tests/test_web_app.py`
  - `python3 -m unittest -v tests.test_smoke tests.test_web_app`
  - `git diff --check`
  - `rg -n "response-correction-save-request|corrected_text|save_content_source|source_message_id|preview_markdown|approval snapshot|기록된 수정본|저장 요청" app/templates/index.html app/web.py tests/test_smoke.py tests/test_web_app.py docs/PRODUCT_SPEC.md docs/ARCHITECTURE.md docs/ACCEPTANCE_CRITERIA.md docs/MILESTONES.md docs/TASK_BACKLOG.md docs/NEXT_STEPS.md README.md`
- 미실행:
  - `python3 -m unittest -v`
  - `make e2e-test`

## 남은 리스크
- 이전 closeout에서 남아 있던 “bridge action visibility 정책 미확정” 리스크는 이번 라운드에서 always-visible + disabled-helper policy로 해소했습니다.
- 이전 closeout에서 남아 있던 “latest corrected_text와 immutable snapshot wording 사이의 truthfulness 부족” 리스크도 correction area, approval card, corrected-save save-result wording까지 포함해 1차 해소했습니다.
- 다만 현재 approval card는 “최신 수정본과 달라질 수 있다”는 계약을 정직하게 설명할 뿐, pending snapshot과 최신 recorded correction의 실제 diff를 별도 stale-indicator로 계산해 보여 주지는 않습니다.
- 또한 이번 검증은 focused unittest와 template-source assertion 중심입니다. 실제 브라우저 상호작용 수준의 E2E 확인은 아직 돌리지 않았으므로, copy 노출 타이밍과 selector 계약은 다음 데모 전 `make e2e-test`로 한 번 더 확인하는 편이 안전합니다.
