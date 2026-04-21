# 2026-04-21 github upload prep verification fixes

## 변경 파일
- `pipeline_runtime/cli.py`
- `tests/test_pipeline_gui_setup.py`
- `docs/ACCEPTANCE_CRITERIA.md`
- `docs/NEXT_STEPS.md`
- `work/4/21/2026-04-21-github-upload-prep-verification-fixes.md`

## 사용 skill
- `github:yeet`: 현재 워크트리를 커밋/푸시하고 draft PR을 만들기 위한 범위 확인, 검증, publish 절차를 따랐습니다.
- `doc-sync`: README smoke inventory 126개와 acceptance/next-step 문서 수치가 어긋난 것을 구현/테스트 진실에 맞춰 동기화했습니다.
- `work-log-closeout`: 업로드 준비 중 실제 수정한 검증 실패와 실행한 체크를 한국어 closeout 형식으로 기록했습니다.

## 변경 이유
- GitHub 업로드 전 전체 `pytest`에서 docs smoke inventory 수치 불일치, pytest xunit hook 오인, Codex update prompt 자동 dismiss 회귀가 드러났습니다.
- 세 실패는 업로드 전 좁게 고칠 수 있는 검증 준비 이슈였고, 기존 문서-first MVP 범위를 넓히지 않았습니다.

## 핵심 변경
- `docs/ACCEPTANCE_CRITERIA.md`와 `docs/NEXT_STEPS.md`의 Playwright smoke inventory count를 README 목록 끝 번호와 같은 126으로 맞췄습니다.
- `tests/test_pipeline_gui_setup.py`의 `setup_module` import alias를 `setup_gui_module`로 바꿔 pytest가 xunit setup hook으로 오인하지 않게 했습니다.
- `pipeline_runtime/cli.py`의 Codex update prompt auto-dismiss marker를 실제 프롬프트 변형에 맞게 `update available` + `skip until next version` 중심으로 좁혔습니다.

## 검증
- `python3 -m pytest -q tests/test_docs_sync.py::BrowserSmokeInventoryDocsParityTest tests/test_pipeline_runtime_cli.py::WrapperEmitterTest::test_codex_update_prompt_is_auto_dismissed_with_skip_until_next_version tests/test_pipeline_runtime_cli.py::WrapperEmitterTest::test_codex_update_prompt_is_not_misclassified_as_ready tests/test_pipeline_gui_setup.py`
  - `9 passed in 0.13s`
- `python3 -m pytest -q`
  - `1447 passed, 1 skipped, 104 subtests passed in 213.31s`
- `npm test -- --reporter=line` in `e2e/`
  - `132 passed (15.9m)`
- `git diff --cached --check`
  - 출력 없음, `rc=0`

## 남은 리스크
- `.pipeline/live-blocked-smoke-*`, `tmp/`, `errlog/`, `projectH-selected-files-20260420-115143.zip`, `file,`, `file.`는 임시/로컬 산출물로 판단해 이번 GitHub 업로드 커밋에는 포함하지 않았습니다.
- Playwright 출력에 `NO_COLOR`/`FORCE_COLOR` 경고와 scanned PDF fixture의 `incorrect startxref pointer(3)` 로그가 있었지만, 테스트 결과는 통과였습니다.
