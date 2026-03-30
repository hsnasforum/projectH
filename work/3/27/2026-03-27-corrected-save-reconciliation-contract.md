# 2026-03-27 corrected-save-reconciliation-contract

## 변경 파일
- `docs/PRODUCT_SPEC.md`
- `docs/ARCHITECTURE.md`
- `docs/ACCEPTANCE_CRITERIA.md`
- `docs/MILESTONES.md`
- `docs/TASK_BACKLOG.md`
- `docs/NEXT_STEPS.md`
- `plandoc/2026-03-27-corrected-save-reconciliation-contract.md`
- `work/3/27/2026-03-27-corrected-save-reconciliation-contract.md`

## 사용 skill
- `mvp-scope`: current shipped contract와 next reconciliation target을 분리한 채 `Option B`를 권고안으로 고정했습니다.
- `frontend-skill`: response card 안에서 correction action과 future corrected-save bridge action을 어떻게 semantic하게 분리할지 restraint 있게 정리했습니다.
- `doc-sync`: root docs와 plandoc 문구를 같은 계약으로 맞췄습니다.
- `release-check`: 실제 실행한 검증만 남기고 미실행 검증을 분리했습니다.
- `work-log-closeout`: 이번 문서 라운드 closeout을 표준 섹션으로 남겼습니다.

## 변경 이유
- 이전 closeout에서 이어받은 핵심 리스크는 correction submit 이후 save approval가 original draft를 계속 대상으로 볼지, corrected text를 later explicit action으로 저장 대상으로 올릴 수 있게 할지 아직 계약으로 고정되지 않았다는 점이었습니다.
- 이번 라운드에서는 current shipped truth와 next reconciliation target을 분리한 채, 자동 rebase 금지 원칙 위에서 한 가지 권고안을 고정해야 했습니다.
- 특히 correction submit과 save approval를 같은 행동처럼 문서화하면 local-first, approval-safe, auditability가 흐려질 위험이 있었습니다.

## 핵심 변경
- `Option B`를 최종 권고안으로 고정했습니다.
  - current original-draft save approval는 그대로 유지
  - corrected text는 later explicit action으로만 save approval 대상이 될 수 있음
  - auto-rebase는 계속 금지
- response card action contract를 정리했습니다.
  - correction submit은 content-edit area
  - future corrected-save bridge action도 response card에서 explicit save-request copy로만 노출
  - actual approval preview / approve / reject / reissue는 approval surface에 유지
- trace / acceptance contract를 분리했습니다.
  - corrected submit 성공
  - original-draft save approval 성공
  - future corrected-save approval 성공
  - 이 셋을 별도 acceptance 축으로 보도록 문서에 고정했습니다.
- root docs와 새 plandoc에 current truth, next reconciliation target, future trace requirement를 같은 방향으로 반영했습니다.

## 검증
- 실행함:
  - `git diff --check`
  - `rg -n "corrected_text|corrected_outcome|save approval|approval preview|rejected|reconciliation|correction editor" docs/PRODUCT_SPEC.md docs/ARCHITECTURE.md docs/ACCEPTANCE_CRITERIA.md docs/MILESTONES.md docs/TASK_BACKLOG.md docs/NEXT_STEPS.md README.md plandoc/2026-03-27-corrected-save-reconciliation-contract.md`
- 미실행:
  - `python3 -m py_compile ...`
  - `python3 -m unittest -v ...`
  - `make e2e-test`

## 남은 리스크
- 이전 closeout에서 남아 있던 “corrected text와 save approval reconciliation contract 부재” 리스크는 문서 수준에서 해소했습니다.
- 이번 라운드에서 일부러 남긴 리스크:
  - corrected-save approval 자체는 아직 미구현입니다.
  - current pending approval preview는 계속 original draft 기준이며, corrected text 저장은 아직 실제 UI action으로 노출되지 않습니다.
  - content-level `rejected` surface는 계속 future work입니다.
- 여전히 남은 open question:
  - future corrected-save trace에서 save-target discriminator field name을 무엇으로 고정할지
