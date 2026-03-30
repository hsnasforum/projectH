# 2026-03-27 corrected-save-bridge-and-snapshot-contract

## 변경 파일
- `docs/PRODUCT_SPEC.md`
- `docs/ARCHITECTURE.md`
- `docs/ACCEPTANCE_CRITERIA.md`
- `docs/MILESTONES.md`
- `docs/TASK_BACKLOG.md`
- `docs/NEXT_STEPS.md`
- `plandoc/2026-03-27-corrected-save-bridge-and-snapshot-contract.md`
- `work/3/27/2026-03-27-corrected-save-bridge-and-snapshot-contract.md`

## 사용 skill
- `mvp-scope`: current shipped truth와 future corrected-save bridge target을 분리한 채 scope를 고정했습니다.
- `doc-sync`: root docs와 새 plandoc 문구를 같은 계약으로 맞췄습니다.
- `release-check`: 실제 실행한 검증만 남기고 미실행 검증을 분리했습니다.
- `work-log-closeout`: 이번 문서 라운드 closeout을 표준 섹션으로 정리했습니다.

## 변경 이유
- 직전 closeout에서 이어받은 핵심 리스크는 future corrected-save approval가 들어올 때, bridge action과 immutable snapshot contract가 아직 비어 있어 구현 시점에 다시 해석이 흔들릴 수 있다는 점이었습니다.
- 특히 `save_content_source = corrected_text`만 추가하면 충분한지, 아니면 별도 snapshot identity가 필요한지 아직 줄이지 못한 상태였습니다.
- 이번 라운드에서는 corrected-save approval 자체를 구현하지 않고도, future bridge action과 audit contract를 먼저 고정해 현재 original-draft save flow와 future corrected-save flow를 섞지 않도록 해야 했습니다.

## 핵심 변경
- future corrected-save는 response card content-edit area에서 시작하는 별도 bridge action으로만 들어가도록 고정했습니다.
- bridge action은 `수정본 기록`과 분리된 save-request action이며, recorded `corrected_text`만 소비하고 unsaved editor state는 직접 approval snapshot으로 올리지 않도록 정리했습니다.
- corrected-save approval snapshot은 request-time `corrected_text`로 생성된 immutable `preview_markdown` / `note_text` body를 가져야 하고, 이후 correction submit으로 rebasing되지 않도록 문서에 고정했습니다.
- future corrected-save trace는 current `save_content_source = original_draft`를 `corrected_text`로 확장하되, same `artifact_id`, same `source_message_id`, same `approval/write` surfaces를 재사용하도록 정리했습니다.
- first corrected-save slice에서는 separate `snapshot_id`를 늘리지 않고, `approval_id`와 frozen approval body를 immutable snapshot identity로 쓰는 쪽으로 open question을 줄였습니다.

## 검증
- 실행:
  - `git diff --check`
  - `rg -n "save_content_source|corrected-save|corrected_text|approval preview|snapshot|immutable|rejected" docs/PRODUCT_SPEC.md docs/ARCHITECTURE.md docs/ACCEPTANCE_CRITERIA.md docs/MILESTONES.md docs/TASK_BACKLOG.md docs/NEXT_STEPS.md README.md plandoc/2026-03-27-corrected-save-bridge-and-snapshot-contract.md`
- 미실행:
  - `python3 -m py_compile ...`
  - `python3 -m unittest -v ...`
  - `make e2e-test`

## 남은 리스크
- 이전 closeout에서 남아 있던 “bridge action과 immutable snapshot contract 부재” 리스크는 문서 수준에서 해소했습니다.
- 이번 라운드에서 줄인 open question은 다음입니다.
  - field name은 계속 `save_content_source`로 유지
  - first corrected-save slice에서는 separate `snapshot_id`를 추가하지 않음
  - `approval_id`와 frozen approval body를 snapshot identity로 사용
- 여전히 남은 리스크는 future UI에서 bridge action을 항상 보이게 둘지, recorded `corrected_text`가 있을 때만 노출할지를 아직 구현 시점 결정으로 남겨 둔 점입니다.
