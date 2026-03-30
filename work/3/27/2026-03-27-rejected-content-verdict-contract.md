# 2026-03-27 rejected content verdict contract

## 변경 파일
- `docs/PRODUCT_SPEC.md`
- `docs/ARCHITECTURE.md`
- `docs/ACCEPTANCE_CRITERIA.md`
- `docs/MILESTONES.md`
- `docs/TASK_BACKLOG.md`
- `docs/NEXT_STEPS.md`
- `plandoc/2026-03-27-rejected-content-verdict-contract.md`
- `work/3/27/2026-03-27-rejected-content-verdict-contract.md`

## 사용 skill
- `frontend-skill`: response-card action separation을 문서 설계 관점으로만 좁게 검토해, content-verdict control을 correction submit / corrected-save / approval controls와 분리된 utility action으로 정리했습니다.
- `doc-sync`: current shipped truth와 next rejected slice contract를 제품 문서와 roadmap 문서에 맞춰 동기화했습니다.
- `release-check`: 실제 실행한 검증만 closeout에 반영하고, 미실행 검증은 주장하지 않도록 점검했습니다.
- `work-log-closeout`: 이번 설계 라운드의 변경 범위, 검증, 남은 리스크를 표준 `/work` 형식으로 정리했습니다.

## 변경 이유
- 직전 closeout에서는 corrected-save first bridge path의 browser smoke와 문서 동기화가 정리되었지만, content-level `rejected`를 truthfully 기록할 explicit control contract는 여전히 고정되지 않았습니다.
- 현재 구현과 문서는 이미 approval reject, no-save, retry, feedback `incorrect`가 content reject가 아니라는 점을 말하고 있으므로, 다음 구현 slice 전에 distinct content-verdict control과 trace / reason contract를 먼저 문서로 고정할 필요가 있었습니다.
- 이번 라운드는 코드 변경 없이, current shipped contract와 next truthful reject surface를 분리해서 정리하는 문서 작업으로 제한했습니다.

## 핵심 변경
- `rejected`는 approval surface가 아니라 grounded-brief response card의 distinct content-verdict action으로만 기록한다는 계약을 고정했습니다.
- 첫 control은 one-click utility action 예시인 `내용 거절`로 정의하고, `수정본 기록`, corrected-save bridge, approval reject와 시각적/의미적으로 분리한다고 정리했습니다.
- source of truth는 original grounded-brief source message로 유지하고, 첫 reject slice는 separate reject store 대신 기존 `corrected_outcome` envelope를 확장해 `outcome = rejected`를 기록하는 쪽으로 고정했습니다.
- reject reason contract는 아주 좁게 고정했습니다:
  - `reason_scope = content_reject`
  - `reason_label = explicit_content_rejection`
  - optional `reason_note`
- approval reject labels와 approval-linked `approval_reason_record`는 content verdict에 재사용하지 않는다고 명시했습니다.
- MVP 권고는 “계약만 두고 더 미루기”가 아니라, corrected-save contract가 안정된 지금 이 explicit rejected control을 next implementation slice로 올리는 쪽으로 정리했습니다.

## 검증
- 실행함: `git diff --check`
- 실행함: `rg -n "rejected|content-verdict|approval reject|corrected-save|incorrect|no-save|retry" docs/PRODUCT_SPEC.md docs/ARCHITECTURE.md docs/ACCEPTANCE_CRITERIA.md docs/MILESTONES.md docs/TASK_BACKLOG.md docs/NEXT_STEPS.md README.md plandoc/2026-03-27-rejected-content-verdict-contract.md`
- 미실행:
  - 제품 코드 검증
  - `python3 -m unittest -v tests.test_smoke tests.test_web_app`
  - `make e2e-test`

## 남은 리스크
- 이전 closeout에서 남아 있던 corrected-save reissue / overwrite edge, stale snapshot diff indicator 부재 같은 구현 리스크는 이번 문서 작업에서 바꾸지 않았고 그대로 남아 있습니다.
- 이번 라운드에서 해소한 리스크는 `rejected`가 approval reject와 섞이지 않도록 하기 위한 explicit control / trace / reason contract 부재였습니다.
- 여전히 남은 리스크는 이 계약이 아직 코드와 테스트로 구현되지는 않았다는 점입니다.
- 또한 first rejected slice에서 optional `reason_note`를 바로 받을지, action-only로 먼저 시작할지는 아직 `OPEN QUESTION`입니다.
