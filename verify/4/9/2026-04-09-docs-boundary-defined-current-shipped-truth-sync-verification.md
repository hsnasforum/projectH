# docs: boundary_defined current-shipped wording truth sync verification

## 변경 파일
- `verify/4/9/2026-04-09-docs-boundary-defined-current-shipped-truth-sync-verification.md`
- `.pipeline/claude_handoff.md`

## 사용 skill
- `round-handoff`

## 변경 이유
- 최신 `/work` note의 `reviewed_memory_boundary_defined` 문구 수정이 실제 문서 상태와 구현 근거에 맞는지 다시 확인해야 했습니다.
- truth가 맞다면 같은 reviewed-memory precondition family 안에서 다음 Claude 슬라이스를 한 개로 고정해야 했습니다.

## 핵심 변경
- 최신 `/work` 는 truthful했습니다.
  - `docs/PRODUCT_SPEC.md:1129`
  - `docs/ARCHITECTURE.md:860`
  - `docs/ACCEPTANCE_CRITERIA.md:643`
  의 `reviewed_memory_boundary_defined` 의미 줄은 이제 이미 출하된 local persistence/apply boundary를 `reviewed_memory_boundary_draft` 와 internal proof-record/store layer 기준으로 설명합니다.
- 이 문구는 현재 구현/테스트와 맞습니다.
  - `app/serializers.py:1138`
  - `app/serializers.py:1432`
  - `app/serializers.py:1480`
  - `tests/test_web_app.py:1223`
  - `tests/test_web_app.py:1304`
  - `tests/test_web_app.py:1321`
- 다음 Claude 슬라이스는 같은 family의 바로 위 summary residual로 고정했습니다.
  - `docs/PRODUCT_SPEC.md:1059-1062`
  - `docs/ARCHITECTURE.md:798-802`
  - `docs/ACCEPTANCE_CRITERIA.md:585-589`
  는 아직 reviewed memory를 `later` layer처럼 넓게 적지만, 현재 shipped root docs와 구현은 read-only contract objects와 apply path를 이미 current surface로 잠그고 있습니다.

## 검증
- `sed -n '1,260p' work/4/9/2026-04-09-docs-boundary-defined-current-shipped-truth-sync.md`
- `nl -ba docs/PRODUCT_SPEC.md | sed -n '1126,1134p'`
- `nl -ba docs/ARCHITECTURE.md | sed -n '858,862p'`
- `nl -ba docs/ACCEPTANCE_CRITERIA.md | sed -n '641,646p'`
- `nl -ba docs/PRODUCT_SPEC.md | sed -n '1056,1064p'`
- `nl -ba docs/ARCHITECTURE.md | sed -n '796,804p'`
- `nl -ba docs/ACCEPTANCE_CRITERIA.md | sed -n '583,590p'`
- `nl -ba app/serializers.py | sed -n '1138,1158p'`
- `nl -ba app/serializers.py | sed -n '1432,1498p'`
- `nl -ba app/handlers/aggregate.py | sed -n '392,636p'`
- `nl -ba tests/test_web_app.py | sed -n '1210,1328p'`
- `rg -n "later reviewed-memory layer|future reviewed memory remains a later|later reviewed-memory transition above the blocked marker|later reviewed memory" docs/PRODUCT_SPEC.md docs/ARCHITECTURE.md docs/ACCEPTANCE_CRITERIA.md`
- `git diff --check`
- Python unit test와 Playwright는 이번 검증 라운드에서 재실행하지 않았습니다.

## 남은 리스크
- root authority docs의 source-message trace vs reviewed-memory layer summary가 아직 current shipped contract-object/apply path를 `later reviewed memory`처럼 넓게 묶어 읽히게 합니다.
