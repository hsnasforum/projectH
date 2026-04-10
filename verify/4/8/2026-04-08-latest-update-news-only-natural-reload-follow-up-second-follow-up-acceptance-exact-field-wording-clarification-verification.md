# latest-update news-only natural-reload follow-up + second-follow-up acceptance exact-field wording clarification verification

날짜: 2026-04-08

## 변경 파일
- `verify/4/8/2026-04-08-latest-update-news-only-natural-reload-follow-up-second-follow-up-acceptance-exact-field-wording-clarification-verification.md`
- `.pipeline/claude_handoff.md`

## 사용 skill
- `round-handoff`

## 변경 이유
- latest `/work`는 latest-update news-only natural-reload follow-up + second-follow-up acceptance wording 2줄을 `response-origin exact-field drift 없음`으로 정렬했다고 보고했습니다. 이번 라운드에서는 그 docs-only closeout이 current tree 기준으로 실제 반영됐는지 다시 확인해야 했습니다.
- same-day latest `/verify`와 current `.pipeline/claude_handoff.md`는 직전 single-source natural-reload follow-up + second-follow-up acceptance verification/handoff에 머물러 있었으므로, newer `/work` 기준으로 persistent truth를 다시 고정하고, wording family가 current tree상 닫혔는지 확인한 뒤 다음 한 슬라이스를 다시 골라야 했습니다.

## 핵심 변경
- latest `/work`는 truthful했습니다. current [docs/ACCEPTANCE_CRITERIA.md](/home/xpdlqj/code/projectH/docs/ACCEPTANCE_CRITERIA.md#L1387), [docs/ACCEPTANCE_CRITERIA.md](/home/xpdlqj/code/projectH/docs/ACCEPTANCE_CRITERIA.md#L1388)은 `/work` 주장대로 `response-origin exact-field drift 없음` wording으로 반영돼 있습니다.
- `/work`가 주장한 docs-only verification도 재현됐습니다. `git diff -- docs/ACCEPTANCE_CRITERIA.md`는 empty였고, `git diff --check -- docs/ACCEPTANCE_CRITERIA.md`는 clean이었습니다.
- latest-update natural-reload acceptance exact-field wording family는 current tree 기준으로 닫혔습니다. current [docs/ACCEPTANCE_CRITERIA.md](/home/xpdlqj/code/projectH/docs/ACCEPTANCE_CRITERIA.md#L1389), [docs/ACCEPTANCE_CRITERIA.md](/home/xpdlqj/code/projectH/docs/ACCEPTANCE_CRITERIA.md#L1390), [docs/ACCEPTANCE_CRITERIA.md](/home/xpdlqj/code/projectH/docs/ACCEPTANCE_CRITERIA.md#L1391), [docs/ACCEPTANCE_CRITERIA.md](/home/xpdlqj/code/projectH/docs/ACCEPTANCE_CRITERIA.md#L1392)와 current smoke titles [e2e/tests/web-smoke.spec.mjs](/home/xpdlqj/code/projectH/e2e/tests/web-smoke.spec.mjs#L5972), [e2e/tests/web-smoke.spec.mjs](/home/xpdlqj/code/projectH/e2e/tests/web-smoke.spec.mjs#L6041), [e2e/tests/web-smoke.spec.mjs](/home/xpdlqj/code/projectH/e2e/tests/web-smoke.spec.mjs#L6113), [e2e/tests/web-smoke.spec.mjs](/home/xpdlqj/code/projectH/e2e/tests/web-smoke.spec.mjs#L6180)도 이미 direct exclusion wording으로 정렬돼 있었습니다.
- 다음 슬라이스는 `browser file/folder picker scanned-PDF OCR-not-supported guidance + skipped-PDF partial-failure smoke coverage`로 고정했습니다.
- 근거는 current shipped contract [README.md](/home/xpdlqj/code/projectH/README.md#L66), [README.md](/home/xpdlqj/code/projectH/README.md#L67), [docs/ACCEPTANCE_CRITERIA.md](/home/xpdlqj/code/projectH/docs/ACCEPTANCE_CRITERIA.md#L33), [docs/ACCEPTANCE_CRITERIA.md](/home/xpdlqj/code/projectH/docs/ACCEPTANCE_CRITERIA.md#L34), [docs/ACCEPTANCE_CRITERIA.md](/home/xpdlqj/code/projectH/docs/ACCEPTANCE_CRITERIA.md#L35)가 browser-visible PDF/OCR behavior를 이미 약속하고 있고, service/unit coverage [tests/test_smoke.py](/home/xpdlqj/code/projectH/tests/test_smoke.py#L7518), [tests/test_smoke.py](/home/xpdlqj/code/projectH/tests/test_smoke.py#L7556), [tests/test_web_app.py](/home/xpdlqj/code/projectH/tests/test_web_app.py#L6056)는 존재하지만, current [e2e/tests/web-smoke.spec.mjs](/home/xpdlqj/code/projectH/e2e/tests/web-smoke.spec.mjs)에는 `PDF`, `OCR`, `scanned`, `image-only` browser smoke가 아직 없기 때문입니다.
- current e2e는 이미 [e2e/tests/web-smoke.spec.mjs](/home/xpdlqj/code/projectH/e2e/tests/web-smoke.spec.mjs#L174), [e2e/tests/web-smoke.spec.mjs](/home/xpdlqj/code/projectH/e2e/tests/web-smoke.spec.mjs#L193)의 `browser-file-input` / `browser-folder-input` upload helper를 갖고 있으므로, 이 shipped browser flow의 current-risk reduction을 한 coherent slice로 닫는 편이 가장 작고 truthful합니다.

## 검증
- `sed -n '1,220p' AGENTS.md`
- `sed -n '1,220p' work/README.md`
- `sed -n '1,220p' verify/README.md`
- `sed -n '1,220p' .pipeline/README.md`
- `sed -n '1,220p' .agents/skills/round-handoff/SKILL.md`
- `sed -n '1,220p' work/4/8/2026-04-08-latest-update-news-only-natural-reload-follow-up-second-follow-up-acceptance-exact-field-wording-clarification.md`
- `sed -n '1,260p' verify/4/8/2026-04-08-latest-update-single-source-natural-reload-follow-up-second-follow-up-acceptance-exact-field-wording-clarification-verification.md`
- `sed -n '1,260p' .pipeline/claude_handoff.md`
- `nl -ba docs/ACCEPTANCE_CRITERIA.md | sed -n '1387,1393p'`
- `nl -ba README.md | sed -n '178,183p'`
- `nl -ba docs/MILESTONES.md | sed -n '94,96p'`
- `nl -ba docs/TASK_BACKLOG.md | sed -n '85,90p'`
- `rg -n "latest-update news-only 자연어 reload 후 follow-up|latest-update news-only 자연어 reload 후 두 번째 follow-up|noisy community|보조 커뮤니티|brunch" e2e/tests/web-smoke.spec.mjs`
- `find work/4/8 -maxdepth 1 -type f | sort | rg "latest-update-news-only-natural-reload-follow-up-second-follow-up-acceptance|noisy-community.*natural-reload|milestone-exclusion-wording|acceptance-exact-field-wording"`
- `git diff -- docs/ACCEPTANCE_CRITERIA.md`
- `git diff --check -- docs/ACCEPTANCE_CRITERIA.md`
- `sed -n '1,220p' work/4/8/2026-04-08-latest-update-noisy-community-natural-reload-follow-up-second-follow-up-exclusion-exact-field-wording-clarification.md`
- `sed -n '1,220p' work/4/8/2026-04-08-latest-update-noisy-community-natural-reload-follow-up-second-follow-up-milestone-exclusion-wording-clarification.md`
- `rg -n "latest-update noisy-community natural-reload|noisy-community.*acceptance|noisy community source browser 자연어 reload" verify/4/8`
- `nl -ba e2e/tests/web-smoke.spec.mjs | sed -n '6106,6185p'`
- `nl -ba README.md | sed -n '182,183p'`
- `nl -ba docs/MILESTONES.md | sed -n '95,96p'`
- `nl -ba docs/TASK_BACKLOG.md | sed -n '87,90p'`
- `nl -ba docs/ACCEPTANCE_CRITERIA.md | sed -n '1389,1392p'`
- `test -e verify/4/8/2026-04-08-latest-update-noisy-community-natural-reload-follow-up-second-follow-up-exclusion-exact-field-wording-clarification-verification.md && echo noisy_natural_verify_exists`
- `rg -n "PDF|pdf|OCR|ocr|scanned|image-only" e2e/tests/web-smoke.spec.mjs tests/test_smoke.py tests/test_web_app.py`
- `rg -n "feedback label|feedback|reason" README.md docs/ACCEPTANCE_CRITERIA.md tests/test_smoke.py tests/test_web_app.py e2e/tests/web-smoke.spec.mjs`
- `rg -n "web-search history storage|web search history|search history" README.md docs/ACCEPTANCE_CRITERIA.md tests/test_smoke.py tests/test_web_app.py e2e/tests/web-smoke.spec.mjs`
- `nl -ba docs/MILESTONES.md | sed -n '1,120p'`
- `nl -ba README.md | sed -n '60,70p'`
- `nl -ba docs/ACCEPTANCE_CRITERIA.md | sed -n '30,40p'`
- `nl -ba tests/test_smoke.py | sed -n '7518,7595p'`
- `nl -ba tests/test_web_app.py | sed -n '6056,6090p'`
- `rg -n "setInputFiles|input\\[type=file\\]|upload|source_path|search_root" e2e/tests/web-smoke.spec.mjs | head -n 80`
- `rg -n "file_input|pick|browse|source-path|search-root" app core templates e2e/tests/web-smoke.spec.mjs`
- `git status --short -- .pipeline/claude_handoff.md verify/4/8/2026-04-08-latest-update-news-only-natural-reload-follow-up-second-follow-up-acceptance-exact-field-wording-clarification-verification.md`
- `git diff --check -- .pipeline/claude_handoff.md`
- `git diff --no-index --check /dev/null verify/4/8/2026-04-08-latest-update-news-only-natural-reload-follow-up-second-follow-up-acceptance-exact-field-wording-clarification-verification.md`
- Playwright rerun, `python3 -m unittest -v`, `make e2e-test`는 이번 docs-only verification 범위를 넘어가므로 재실행하지 않았습니다.

## 남은 리스크
- latest-update natural-reload acceptance wording family는 현재 tree 기준으로 닫혔지만, shipped browser-visible PDF/OCR path는 아직 Playwright smoke로 재현되지 않았습니다.
- 이번 verification은 latest docs-only `/work` truth와 next slice selection까지만 다뤘으므로, browser/runtime health 자체는 다시 판정하지 않았습니다.
