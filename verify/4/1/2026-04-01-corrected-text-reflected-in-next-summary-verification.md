# 2026-04-01 corrected_text reflected in next summary verification

## 변경 파일
- `verify/4/1/2026-04-01-corrected-text-reflected-in-next-summary-verification.md`
- `.pipeline/codex_feedback.md`

## 사용 skill
- `round-handoff`

## 변경 이유
- latest `/work`인 `work/4/1/2026-04-01-corrected-text-reflected-in-next-summary.md`의 round-local 코드/테스트 변경 주장이 실제로 맞는지 확인했습니다.
- same-day latest `/verify`인 `verify/4/1/2026-04-01-search-result-preview-response-path-regression-verification.md` 이후의 이번 라운드가 current `projectH` 방향 안에서 좁게 진행됐는지 확인했습니다.
- 이번 변경에 필요한 최소 검증만 재실행하고, 다음 Claude handoff를 현재 truth에 맞게 다시 좁혔습니다.

## 핵심 변경
- latest `/work`의 코드 변경 주장은 맞았습니다. 이번 라운드의 round-local product-file 변경은 [storage/session_store.py](/home/xpdlqj/code/projectH/storage/session_store.py#L891)와 [tests/test_smoke.py](/home/xpdlqj/code/projectH/tests/test_smoke.py#L4168)에 한정되어 있었고, `record_correction_for_message`가 교정 저장 뒤 현재 세션 `active_context.summary_hint`를 `corrected_text` 기반으로 갱신하도록 바뀌었습니다.
- 추가된 smoke regression 2건도 실제로 존재했고, [tests/test_smoke.py](/home/xpdlqj/code/projectH/tests/test_smoke.py#L4168)와 [tests/test_smoke.py](/home/xpdlqj/code/projectH/tests/test_smoke.py#L4224)에서 각각 summary hint 갱신과 no-active-context 안전 처리를 잠그고 있습니다.
- 범위는 grounded-brief correction이 같은 세션 후속 요약에 반영되도록 만드는 summary-quality slice로, current document-first MVP 방향을 벗어나지 않았습니다. whole-project audit 징후도 없어 `report/`는 만들지 않았습니다.
- 다만 closeout은 docs 기준으로 fully truthful하지 않습니다. 현재 correction contract를 설명하는 [README.md](/home/xpdlqj/code/projectH/README.md#L39), [docs/PRODUCT_SPEC.md](/home/xpdlqj/code/projectH/docs/PRODUCT_SPEC.md#L411), [docs/ACCEPTANCE_CRITERIA.md](/home/xpdlqj/code/projectH/docs/ACCEPTANCE_CRITERIA.md#L177)에는 `corrected_text`가 같은 세션의 다음 요약/후속 요약 기준(`active_context.summary_hint`)도 갱신한다는 shipped behavior가 반영되어 있지 않습니다.
- 기존 `.pipeline/codex_feedback.md`는 `STATUS: implement`인데도 operator가 다음 슬라이스를 고르라고 적어 control signal이 모순되어 있었으므로, 이번 검증 라운드에서 exact docs-only slice로 다시 썼습니다.

## 검증
- `python3 -m py_compile storage/session_store.py`: 통과
- `python3 -m unittest -v tests.test_smoke tests.test_web_app`: `Ran 281 tests`, `OK`
- `git diff --check -- storage/session_store.py tests/test_smoke.py`: 통과
- `README.md`, `docs/PRODUCT_SPEC.md`, `docs/ACCEPTANCE_CRITERIA.md`의 correction-contract 구간을 구현과 대조했고, 이번 라운드 shipped behavior를 설명하는 문구가 빠져 있음을 확인했습니다.
- browser smoke는 이번 라운드가 storage-level behavior와 smoke regression 보강만 바꿨고 브라우저 계약 자체를 바꾸지 않아 재실행하지 않았습니다.

## 남은 리스크
- 가장 작은 same-family 후속은 docs truth sync뿐입니다. 구현 자체는 통과했지만, 문서가 현 shipped behavior를 누락하고 있어 다음 라운드에서 바로 닫는 편이 맞습니다.
- 현재 구현은 교정 시점의 `active_context.summary_hint`를 갱신한다는 전제를 사용합니다. 현 UI는 latest grounded-brief correction 경로라 실질 리스크가 크지 않지만, 나중에 임의의 과거 메시지 교정까지 열리면 active-context anchor 확인이 추가로 필요할 수 있습니다.
- dirty worktree가 넓으니 다음 라운드도 touched 파일만 분명히 적는 편이 안전합니다.
