# 2026-03-31 operator slice governance tightening

## 변경 파일
- `AGENTS.md`
- `CLAUDE.md`
- `PROJECT_CUSTOM_INSTRUCTIONS.md`
- `work/README.md`
- `verify/README.md`
- `.pipeline/README.md`

## 사용 skill
- `doc-sync`
  - single-Codex 운영 규칙과 `/work`·`/verify`·`.pipeline` handoff 정책을 현재 판단 기준에 맞게 동기화했습니다.
- `work-log-closeout`
  - 오늘 라운드의 운영 규칙 변경과 실제 실행한 검증을 closeout 형식으로 정리했습니다.

## 변경 이유
- 최신 canonical 기준선을 `future_reviewed_memory_stop_apply` verified 지점으로 다시 잡은 뒤, 다음 슬라이스가 내부 route completeness나 regression 빈칸 채우기로 자동 미끄러지지 않도록 운영 규칙을 보완할 필요가 있었습니다.
- 기존 문서에는 single-Codex 흐름과 `/work`·`/verify` 경계는 잘 정리되어 있었지만, "검증은 얼마나 좁게 할지", "다음 슬라이스를 무엇 기준으로 고를지", "reviewed-memory를 어디까지 planning anchor로 볼지"에 대한 가드레일이 약했습니다.

## 핵심 변경
- `AGENTS.md`에 아래 운영 가드레일을 추가했습니다.
  - 다음 슬라이스는 user-visible value, concrete risk reduction, shipped contract truthfulness 중 하나를 직접 개선해야 한다는 기준
  - reviewed-memory planning anchor를 user-visible activation + explicit stop 지점까지로 두고, deeper reversal / conflict-visibility / route completeness가 자동 기본값이 되지 않도록 하는 기준
  - verification은 risk-based로 좁게 수행하고, 모든 service/handler 변경에 full browser 검증을 강제하지 않는 기준
- `CLAUDE.md`에 `.pipeline/codex_feedback.md` 해석 규칙을 추가해, handoff가 route-by-route completeness로 끌어갈 때도 current MVP 우선순위를 먼저 보도록 명시했습니다.
- `PROJECT_CUSTOM_INSTRUCTIONS.md`에 `검증 범위 최소화 원칙`, `다음 슬라이스 선정 원칙`을 추가했습니다.
- `work/README.md`, `verify/README.md`, `.pipeline/README.md`에 closeout, verification, handoff가 단순 uncovered regression 채우기로 흘러가지 않도록 하는 운영 문구를 추가했습니다.

## 검증
- `git diff --check`
  - 통과

## 남은 리스크
- 이번 라운드는 운영 규칙 문서 보강만 했으므로 앱 코드나 테스트는 다시 돌리지 않았습니다.
- 실제 다음 라운드에서 Codex가 새 `codex_feedback.md`를 쓸 때, 이번 가드레일을 실제로 적용하는지까지는 아직 검증되지 않았습니다.
- `backup/`으로 옮겨 둔 reviewed-memory 후반부 기록과 현재 canonical `work/`·`verify/` 사이의 경계를 후속 handoff에서 계속 명확히 유지해야 합니다.
