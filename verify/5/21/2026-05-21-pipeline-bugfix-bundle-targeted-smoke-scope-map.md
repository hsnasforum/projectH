# verify: 2026-05-21 pipeline bugfix bundle targeted smoke + scope map

## 대상 work
`work/5/21/2026-05-21-pipeline-bugfix-bundle-targeted-smoke-scope-map.md`

## 검증 결과: READY (그룹 A 한정)

## 재실행 검증

| 검사 | 결과 |
|---|---|
| `test_smoke` 169개 (mock 경로 전체) | PASS |
| `test_web_app -k "not colloquial"` | Ran 0 tests — 필터 미동작, 성공 기준 미충족 |
| fallback: `test_web_app` 20초 head 300줄 | import 단계 즉시 실패 없음 확인 |
| hang 테스트 코드 직접 확인 | `"provider":"ollama"` 강제 확인 → 환경 의존 |
| `ollama serve` 프로세스 확인 | 존재하나 `ollama runner` 없음 → 모델 미로드 |

## 핵심 판정

**그룹 A pipeline_runtime 번들: 회귀 없음, commit 준비 완료**

- `test_smoke` 169개 PASS — mock 기반 web app import 경로 정상
- test_web_app hang: `ollama runner` 미로드 상태에서 `"provider":"ollama"` 강제 호출 → streaming hang. pipeline_runtime 변경과 인과관계 없음

**test_web_app 전체 PASS는 미확인 (환경 의존)**
- full `test_web_app` filtered pass를 얻지 못했으므로 web app 전체 PASS 주장 안 함
- 단, pipeline_runtime import가 web app을 깨는 증거는 없음

## dirty worktree 분류 확인

| 그룹 | 파일 수 | 상태 |
|---|---|---|
| A (pipeline_runtime 번들) | 6 | 검증 완료, commit 준비 완료 |
| B (별도 라운드 산출물) | 33 | operator 결정 필요 |

그룹 A 6개 파일:
- `pipeline_runtime/automation_health.py`
- `pipeline_runtime/cli.py`
- `pipeline_runtime/supervisor.py`
- `tests/test_pipeline_runtime_automation_health.py`
- `tests/test_pipeline_runtime_cli.py`
- `tests/test_pipeline_runtime_supervisor.py`

## 확인하지 않은 항목

- `test_web_app` 전체 filtered pass: Python unittest -k가 제외식 미지원
- Playwright / E2E / live runtime
- 그룹 B 파일 내용 검토

## 다음 operator 결정 사항

1. **그룹 A 단독 커밋** — 6개 파일만 stage, commit (권장)
2. **그룹 B 커밋 범위** — 별도 라운드 산출물을 어떤 단위로 묶을지
3. **test_web_app Ollama hang** — 테스트에 timeout 또는 mock override 추가할지
