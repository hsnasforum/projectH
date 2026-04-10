# latest-update single-source natural-reload browser-anchor source-path-exact-field wording clarification verification

날짜: 2026-04-08

## 변경 파일
- `verify/4/8/2026-04-08-latest-update-single-source-natural-reload-browser-anchor-source-path-exact-field-wording-clarification-verification.md`
- `.pipeline/claude_handoff.md`

## 사용 skill
- `round-handoff`

## 변경 이유
- latest `/work`는 latest-update single-source natural-reload family의 initial/follow-up/second-follow-up title 3개가 exact source-path와 exact field wording으로 정렬됐다고 보고했습니다. 이번 라운드에서는 그 title change와 focused rerun claim이 current tree 기준으로 truthful한지 다시 확인할 필요가 있었습니다.
- 오늘 same-day latest `/verify`는 mixed-source natural-reload verification까지였으므로, 그 다음 family인 single-source natural-reload wording round를 실제로 닫고 latest-update natural-reload family에서 다음 exact slice를 하나로 고정해야 했습니다.

## 핵심 변경
- latest `/work`의 observable end state는 truthful하셨습니다. `e2e/tests/web-smoke.spec.mjs:5456`, `e2e/tests/web-smoke.spec.mjs:5707`, `e2e/tests/web-smoke.spec.mjs:5768`에는 `/work`가 주장한 single-source natural-reload title wording이 실제로 반영돼 있었고, 모두 `example.com/seoul-weather`, `WEB`, `최신 확인`, `단일 출처 참고`, `보조 출처`를 직접 드러냅니다.
- single-source natural-reload body/docs truth도 current tree와 맞았습니다. body는 initial natural-reload continuity `e2e/tests/web-smoke.spec.mjs:5498`, `e2e/tests/web-smoke.spec.mjs:5499`, `e2e/tests/web-smoke.spec.mjs:5502`, `e2e/tests/web-smoke.spec.mjs:5504`, `e2e/tests/web-smoke.spec.mjs:5505`, `e2e/tests/web-smoke.spec.mjs:5508`, follow-up continuity `e2e/tests/web-smoke.spec.mjs:5753`, `e2e/tests/web-smoke.spec.mjs:5754`, `e2e/tests/web-smoke.spec.mjs:5757`, `e2e/tests/web-smoke.spec.mjs:5759`, `e2e/tests/web-smoke.spec.mjs:5760`, `e2e/tests/web-smoke.spec.mjs:5763`, second-follow-up continuity `e2e/tests/web-smoke.spec.mjs:5818`, `e2e/tests/web-smoke.spec.mjs:5819`, `e2e/tests/web-smoke.spec.mjs:5822`, `e2e/tests/web-smoke.spec.mjs:5824`, `e2e/tests/web-smoke.spec.mjs:5825`, `e2e/tests/web-smoke.spec.mjs:5828`에서 same truth를 직접 검증합니다. docs `README.md:172`, `README.md:176`, `README.md:177`, `docs/MILESTONES.md:90`, `docs/MILESTONES.md:93`, `docs/ACCEPTANCE_CRITERIA.md:1381`, `docs/ACCEPTANCE_CRITERIA.md:1385`, `docs/ACCEPTANCE_CRITERIA.md:1386`, `docs/TASK_BACKLOG.md:79`, `docs/TASK_BACKLOG.md:83`, `docs/TASK_BACKLOG.md:84`도 current tree와 정렬돼 있습니다.
- focused rerun은 current tree에서 재현됐습니다. `cd e2e && npx playwright test tests/web-smoke.spec.mjs -g "latest-update single-source 자연어 reload" --reporter=line`은 `3 passed (19.2s)`였습니다. `git diff -- e2e/tests/web-smoke.spec.mjs`는 empty, `git diff --check -- e2e/tests/web-smoke.spec.mjs`는 clean, `rg -c '^test\(' e2e/tests/web-smoke.spec.mjs` 결과는 `75`였습니다.
- latest-update single-source natural-reload wording family는 이번 라운드 기준으로 닫혔습니다. initial `e2e/tests/web-smoke.spec.mjs:5456`, follow-up `e2e/tests/web-smoke.spec.mjs:5707`, second-follow-up `e2e/tests/web-smoke.spec.mjs:5768`이 모두 docs/body truth와 정렬됐습니다.
- 다음 Claude 슬라이스는 `latest-update news-only natural-reload browser-anchor source-path-exact-field wording clarification`으로 고정했습니다. `e2e/tests/web-smoke.spec.mjs:5513`, `e2e/tests/web-smoke.spec.mjs:5833`, `e2e/tests/web-smoke.spec.mjs:5897`의 news-only natural-reload title 3개만 아직 generic wording이고, same body는 initial `e2e/tests/web-smoke.spec.mjs:5557`, `e2e/tests/web-smoke.spec.mjs:5558`, `e2e/tests/web-smoke.spec.mjs:5561`, `e2e/tests/web-smoke.spec.mjs:5563`, `e2e/tests/web-smoke.spec.mjs:5564`, `e2e/tests/web-smoke.spec.mjs:5567`, `e2e/tests/web-smoke.spec.mjs:5568`, follow-up `e2e/tests/web-smoke.spec.mjs:5881`, `e2e/tests/web-smoke.spec.mjs:5882`, `e2e/tests/web-smoke.spec.mjs:5885`, `e2e/tests/web-smoke.spec.mjs:5887`, `e2e/tests/web-smoke.spec.mjs:5888`, `e2e/tests/web-smoke.spec.mjs:5891`, `e2e/tests/web-smoke.spec.mjs:5892`, second-follow-up `e2e/tests/web-smoke.spec.mjs:5949`, `e2e/tests/web-smoke.spec.mjs:5950`, `e2e/tests/web-smoke.spec.mjs:5953`, `e2e/tests/web-smoke.spec.mjs:5955`, `e2e/tests/web-smoke.spec.mjs:5956`, `e2e/tests/web-smoke.spec.mjs:5959`, `e2e/tests/web-smoke.spec.mjs:5960`에서 `hankyung.com`, `mk.co.kr`, `WEB`, `최신 확인`, `기사 교차 확인`, `보조 기사`를 직접 검증합니다. docs `README.md:173`, `README.md:178`, `README.md:179`, `docs/MILESTONES.md:91`, `docs/MILESTONES.md:94`, `docs/ACCEPTANCE_CRITERIA.md:1382`, `docs/ACCEPTANCE_CRITERIA.md:1387`, `docs/ACCEPTANCE_CRITERIA.md:1388`, `docs/TASK_BACKLOG.md:80`, `docs/TASK_BACKLOG.md:85`, `docs/TASK_BACKLOG.md:86`도 이미 same truth를 고정합니다. single-source를 닫은 뒤 남는 same-family current-risk reduction으로는 news-only natural-reload wording family가 가장 작고 자연스럽습니다.

## 검증
- `sed -n '1,260p' AGENTS.md`
- `sed -n '1,220p' work/README.md`
- `sed -n '1,220p' verify/README.md`
- `sed -n '1,220p' .pipeline/README.md`
- `sed -n '1,220p' .agents/skills/round-handoff/SKILL.md`
- `sed -n '1,260p' work/4/8/2026-04-08-latest-update-single-source-natural-reload-browser-anchor-source-path-exact-field-wording-clarification.md`
- `sed -n '1,260p' verify/4/8/2026-04-08-latest-update-mixed-source-natural-reload-browser-anchor-source-path-exact-field-wording-clarification-verification.md`
- `sed -n '1,260p' .pipeline/claude_handoff.md`
- `git status --short`
- `git diff -- e2e/tests/web-smoke.spec.mjs`
- `git diff --check -- e2e/tests/web-smoke.spec.mjs`
- `rg -c '^test\(' e2e/tests/web-smoke.spec.mjs`
- `nl -ba e2e/tests/web-smoke.spec.mjs | sed -n '5456,5905p'`
- `nl -ba e2e/tests/web-smoke.spec.mjs | sed -n '5897,5960p'`
- `nl -ba README.md | sed -n '172,180p'`
- `nl -ba docs/MILESTONES.md | sed -n '90,96p'`
- `nl -ba docs/ACCEPTANCE_CRITERIA.md | sed -n '1381,1389p'`
- `nl -ba docs/TASK_BACKLOG.md | sed -n '79,87p'`
- `cd e2e && npx playwright test tests/web-smoke.spec.mjs -g "latest-update single-source 자연어 reload" --reporter=line`
- `python3 -m unittest -v`, `make e2e-test`는 이번 wording verification 범위를 넘어가므로 재실행하지 않았습니다.

## 남은 리스크
- `latest-update` news-only natural-reload title 3개(`e2e/tests/web-smoke.spec.mjs:5513`, `e2e/tests/web-smoke.spec.mjs:5833`, `e2e/tests/web-smoke.spec.mjs:5897`)는 아직 generic wording입니다. 다음 라운드에서 `hankyung.com`, `mk.co.kr`, `WEB`, `최신 확인`, `기사 교차 확인`, `보조 기사`를 title에 직접 반영하는 편이 가장 작은 same-family current-risk reduction입니다.
- `latest-update` noisy-source family는 이번 verification 범위 밖이라 재판정하지 않았습니다.
