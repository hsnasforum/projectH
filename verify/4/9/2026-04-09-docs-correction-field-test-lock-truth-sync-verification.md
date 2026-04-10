# Docs correction field test-lock truth sync verification

## 변경 파일
- `verify/4/9/2026-04-09-docs-correction-field-test-lock-truth-sync-verification.md`
- `.pipeline/claude_handoff.md`

## 사용 skill
- `round-handoff`

## 변경 이유
- 최신 `/work` `work/4/9/2026-04-09-docs-correction-field-test-lock-truth-sync.md`가 직전 verification note가 고정한 response payload correction-field test-lock wording drift를 실제로 닫았는지 다시 확인하고, 같은 docs family의 다음 단일 current-risk reduction 슬라이스를 좁힐 필요가 있었습니다.
- 같은 날짜의 기존 verification note `verify/4/9/2026-04-09-docs-acceptance-save-content-source-enum-truth-sync-verification.md`를 먼저 읽은 뒤, 그 후속 `/work`가 실제 handoff scope를 끝까지 닫았는지 재검수했습니다.

## 핵심 변경
- 최신 `/work`는 부분적으로 truthful합니다.
  - `docs/ARCHITECTURE.md:167`과 `docs/ACCEPTANCE_CRITERIA.md:121`은 이제 control fields에 더해 `original_response_snapshot`, `corrected_outcome`, `save_content_source`, `approval_reason_record`, `content_reason_record`까지 tests가 잠근다고 적습니다.
  - 이 correction/save anchor 추가 자체는 현재 tree와 맞습니다.
    - `original_response_snapshot` / `corrected_outcome` / `save_content_source`는 `tests/test_web_app.py:6187-6192`, `tests/test_web_app.py:6247-6257`, `tests/test_smoke.py:2718-2731`, `tests/test_smoke.py:4410-4412`, `tests/test_smoke.py:4789-4802`가 잠급니다.
    - `approval_reason_record`는 `tests/test_web_app.py:6391-6398`, `tests/test_web_app.py:7112-7117`, `tests/test_smoke.py:2913-2918`, `tests/test_smoke.py:2990-2994`가 잠급니다.
    - `content_reason_record`는 `tests/test_web_app.py:490-498`, `tests/test_smoke.py:4648-4664`가 잠급니다.
- 하지만 이번 `/work` closeout이 주장한 “응답 페이로드 계약 family 테스트 잠금 진실 동기화 완료”는 아직 과합니다.
  - 두 문서는 여전히 `tests/test_smoke.py`를 `browser smoke tests`로 적고 있습니다 (`docs/ARCHITECTURE.md:167`, `docs/ACCEPTANCE_CRITERIA.md:121`).
  - 실제 `tests/test_smoke.py`는 Python `unittest` 기반 smoke/service suite이며 브라우저 E2E가 아닙니다 (`tests/test_smoke.py:1-14`).
  - 현재 Playwright browser smoke는 `e2e/tests/web-smoke.spec.mjs` 경로에 따로 있습니다 (`e2e/tests/web-smoke.spec.mjs`).
  - repo 다른 docs도 Playwright browser smoke를 별도 surface로 구분합니다 (`README.md:110`, `docs/ARCHITECTURE.md:1313`, `docs/ACCEPTANCE_CRITERIA.md:1344`).
- 따라서 최신 `/work`는 correction/save field anchor drift는 줄였지만, response payload test-lock wording family를 완전히 닫았다고 보기는 어렵습니다.
- 다음 Claude 슬라이스는 `.pipeline/claude_handoff.md`에 `Docs ARCHITECTURE ACCEPTANCE_CRITERIA response payload test-suite label truth sync`로 고정했습니다.

## 검증
- `sed -n '1,240p' .agents/skills/round-handoff/SKILL.md`
- `sed -n '1,260p' AGENTS.md`
- `sed -n '1,220p' work/README.md`
- `sed -n '1,220p' verify/README.md`
- `sed -n '1,220p' .pipeline/README.md`
- `sed -n '1,240p' work/4/9/2026-04-09-docs-correction-field-test-lock-truth-sync.md`
- `sed -n '1,260p' verify/4/9/2026-04-09-docs-acceptance-save-content-source-enum-truth-sync-verification.md`
- `sed -n '1,220p' docs/NEXT_STEPS.md`
- `sed -n '1,220p' docs/MILESTONES.md`
- `sed -n '1,220p' docs/TASK_BACKLOG.md`
- `git status --short`
- `git diff -- docs/ARCHITECTURE.md docs/ACCEPTANCE_CRITERIA.md`
- `git diff --check`
- `nl -ba docs/ARCHITECTURE.md | sed -n '166,168p'`
- `nl -ba docs/ACCEPTANCE_CRITERIA.md | sed -n '120,122p'`
- `rg -n 'original_response_snapshot|corrected_outcome|approval_reason_record|content_reason_record|save_content_source' tests/test_web_app.py tests/test_smoke.py -S`
- `nl -ba tests/test_smoke.py | sed -n '2718,2731p'`
- `nl -ba tests/test_smoke.py | sed -n '2913,2918p'`
- `nl -ba tests/test_smoke.py | sed -n '2990,2994p'`
- `nl -ba tests/test_smoke.py | sed -n '4645,4664p'`
- `sed -n '1,120p' tests/test_smoke.py`
- `rg -n 'Playwright|browser smoke|web-smoke.spec|e2e' docs/ARCHITECTURE.md docs/ACCEPTANCE_CRITERIA.md README.md docs/MILESTONES.md tests/test_smoke.py tests/test_web_app.py -S`
- `ls -1 e2e/tests`
- `sed -n '1,80p' tests/test_web_app.py`
- `sed -n '1,240p' .pipeline/claude_handoff.md`

## 남은 리스크
- 이번 라운드는 docs/code truth 대조와 handoff 갱신만 수행했습니다. Python unit test와 Playwright는 재실행하지 않았습니다.
- `docs/ARCHITECTURE.md:167`과 `docs/ACCEPTANCE_CRITERIA.md:121`은 correction/save anchors는 맞췄지만, 여전히 `tests/test_smoke.py`를 browser smoke로 적고 있어 현재 test-suite labeling truth와 어긋납니다.
- 현재 worktree에는 이 라운드와 무관한 dirty/untracked 파일이 많이 남아 있으므로 다음 슬라이스도 unrelated changes를 건드리지 말아야 합니다.
