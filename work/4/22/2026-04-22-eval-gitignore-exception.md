# 2026-04-22 eval gitignore exception

## 변경 파일
- `.gitignore`
- `work/4/22/2026-04-22-eval-gitignore-exception.md`

## 사용 skill
- `finalize-lite`: handoff 필수 검증, 변경 범위, `/work` closeout 준비 상태를 확인했다.
- `work-log-closeout`: 실제 변경 파일, 실행한 검증, 남은 리스크를 한국어 `/work` 기록으로 남겼다.

## 변경 이유
- `.pipeline/implement_handoff.md` CONTROL_SEQ 831
  (`milestone8_axis2_gitignore_eval_exception`)에 따라 `data/eval/fixtures/correction_reuse_001.json`이
  `data/*` ignore 규칙에 막히지 않도록 했다.
- 기존 `!data/sessions/`, `!data/web-search/` 예외와 같은 패턴으로 `data/eval/`만
  trackable directory로 열었다.

## 핵심 변경
- `.gitignore`의 `data/*` 아래, `!data/.gitkeep` 직후에 `!data/eval/` 한 줄을 추가했다.
- `data/eval/fixtures/correction_reuse_001.json`은 이제 `git status --short data/eval/`에서
  `?? data/eval/`로 표시된다.
- handoff 제한에 따라 `data/eval/fixtures/correction_reuse_001.json`, Python source,
  docs, `.pipeline` control 파일은 수정하지 않았다.

## 검증
- `git check-ignore -v data/eval/fixtures/correction_reuse_001.json` → 통과
  (빈 출력, exit 1: 더 이상 ignore되지 않음)
- `git status --short data/eval/` → 통과 (`?? data/eval/`)
- `python3 -m unittest tests.test_smoke -q` → 통과 (`Ran 150 tests`, `OK`)
- `git diff --check -- .gitignore` → 통과

## 남은 리스크
- 이번 handoff는 ignore 예외만 추가했다. fixture commit/push 여부 판단은 implement lane
  범위가 아니므로 수행하지 않았다.
- 작업 전부터 남아 있던 별도 untracked `/work` 파일과 advisory report, verify note 변경은
  이번 handoff 범위가 아니어서 건드리지 않았다.
