# verify: 2026-05-21 Codex v0.132.0 paste submit fallback

## 대상 work
`work/5/21/2026-05-21-codex-v0132-paste-submit-fallback.md`

## 검증 결과: READY (live 확인 포함)

## 재실행 검증

| 검사 | 결과 |
|---|---|
| `py_compile` watcher_dispatch.py / lane_surface.py | PASS |
| 관련 unittest 58개 | PASS |
| `git diff --check` | PASS |
| live DISPATCH_SEEN → TASK_ACCEPTED 체인 | ✓ 확인 |

## 라이브 이벤트 확인

```
pane_text_fallback_used  Codex BOOTING→READY (초기 기동)
DISPATCH_SEEN            ctrl-2073
TASK_ACCEPTED            ctrl-2073
→ IMPLEMENT_ACTIVE, automation_health=ok
```

TASK_DONE → 다음 DISPATCH_SEEN → TASK_ACCEPTED 체인도 연속 관찰됨.
`pasted_prompt_after_submit` 반복 루프 해소됨.

## 원인 및 수정

| 원인 | 수정 |
|---|---|
| Codex v0.132.0에서 긴 프롬프트가 여러 줄로 접혀 감지 윈도우(12줄) 밖으로 나감 | lane_surface.py 감지 윈도우 확장 |
| Enter/C-j만으로 paste submit 안 되는 경우 발생 | watcher_dispatch.py cleanup 성공 후 one-line literal fallback 추가 |

## 확인하지 않은 항목

- Full smoke / Playwright / long soak (범위 밖)
- Codex v0.132.0 이외 버전에서의 회귀 (기존 unittest로 보호)
