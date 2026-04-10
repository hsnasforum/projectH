# latest-update news-only natural-reload browser-anchor source-path-exact-field wording clarification verification

날짜: 2026-04-08

## 변경 파일
- `verify/4/8/2026-04-08-latest-update-news-only-natural-reload-browser-anchor-source-path-exact-field-wording-clarification-verification.md`
- `.pipeline/claude_handoff.md`

## 사용 skill
- `round-handoff`

## 변경 이유
- latest `/work`는 latest-update news-only natural-reload family의 initial/follow-up/second-follow-up title 3개가 exact source-path와 exact field wording으로 정렬됐다고 보고했습니다. 이번 라운드에서는 그 title change와 focused rerun claim이 current tree 기준으로 truthful한지 다시 확인할 필요가 있었습니다.
- same-day latest `/verify`는 single-source natural-reload verification까지였으므로, 그 다음 family인 news-only natural-reload wording round를 실제로 닫고 latest-update natural-reload family 이후의 다음 exact slice를 하나로 고정해야 했습니다.

## 핵심 변경
- latest `/work`의 observable end state는 truthful하셨습니다. `e2e/tests/web-smoke.spec.mjs:5513`, `e2e/tests/web-smoke.spec.mjs:5833`, `e2e/tests/web-smoke.spec.mjs:5897`에는 `/work`가 주장한 news-only natural-reload title wording이 실제로 반영돼 있었고, 모두 `hankyung.com`, `mk.co.kr`, `WEB`, `최신 확인`, `기사 교차 확인`, `보조 기사`를 직접 드러냅니다.
- news-only natural-reload body/docs truth도 current tree와 맞았습니다. body는 initial continuity `e2e/tests/web-smoke.spec.mjs:5557`, `e2e/tests/web-smoke.spec.mjs:5558`, `e2e/tests/web-smoke.spec.mjs:5561`, `e2e/tests/web-smoke.spec.mjs:5563`, `e2e/tests/web-smoke.spec.mjs:5564`, `e2e/tests/web-smoke.spec.mjs:5567`, `e2e/tests/web-smoke.spec.mjs:5568`, follow-up continuity `e2e/tests/web-smoke.spec.mjs:5881`, `e2e/tests/web-smoke.spec.mjs:5882`, `e2e/tests/web-smoke.spec.mjs:5885`, `e2e/tests/web-smoke.spec.mjs:5887`, `e2e/tests/web-smoke.spec.mjs:5888`, `e2e/tests/web-smoke.spec.mjs:5891`, `e2e/tests/web-smoke.spec.mjs:5892`, second-follow-up continuity `e2e/tests/web-smoke.spec.mjs:5949`, `e2e/tests/web-smoke.spec.mjs:5950`, `e2e/tests/web-smoke.spec.mjs:5953`, `e2e/tests/web-smoke.spec.mjs:5955`, `e2e/tests/web-smoke.spec.mjs:5956`, `e2e/tests/web-smoke.spec.mjs:5959`, `e2e/tests/web-smoke.spec.mjs:5960`에서 same truth를 직접 검증합니다. docs `README.md:173`, `README.md:178`, `README.md:179`, `docs/MILESTONES.md:91`, `docs/MILESTONES.md:94`, `docs/ACCEPTANCE_CRITERIA.md:1382`, `docs/ACCEPTANCE_CRITERIA.md:1387`, `docs/ACCEPTANCE_CRITERIA.md:1388`, `docs/TASK_BACKLOG.md:80`, `docs/TASK_BACKLOG.md:85`, `docs/TASK_BACKLOG.md:86`도 current tree와 정렬돼 있습니다.
- focused rerun은 current tree에서 재현됐습니다. `cd e2e && npx playwright test tests/web-smoke.spec.mjs -g "latest-update news-only 자연어 reload" --reporter=line`은 `3 passed (20.5s)`였습니다. `git diff -- e2e/tests/web-smoke.spec.mjs`는 empty, `git diff --check -- e2e/tests/web-smoke.spec.mjs`는 clean, `rg -c '^test\\(' e2e/tests/web-smoke.spec.mjs` 결과는 `75`였습니다.
- latest-update natural-reload wording family는 이번 라운드 기준으로 mixed-source, single-source, news-only가 모두 닫혔습니다. 다음 Claude 슬라이스는 `latest-update noisy-community natural-reload follow-up + second-follow-up exclusion exact-field wording clarification`으로 고정했습니다. `e2e/tests/web-smoke.spec.mjs:5965`, `e2e/tests/web-smoke.spec.mjs:6034`의 noisy-community natural-reload title 2개만 아직 generic wording이고, same body는 `e2e/tests/web-smoke.spec.mjs:6017`, `e2e/tests/web-smoke.spec.mjs:6018`, `e2e/tests/web-smoke.spec.mjs:6019`, `e2e/tests/web-smoke.spec.mjs:6021`, `e2e/tests/web-smoke.spec.mjs:6022`, `e2e/tests/web-smoke.spec.mjs:6023`, `e2e/tests/web-smoke.spec.mjs:6024`, `e2e/tests/web-smoke.spec.mjs:6026`, `e2e/tests/web-smoke.spec.mjs:6027`, `e2e/tests/web-smoke.spec.mjs:6029`, `e2e/tests/web-smoke.spec.mjs:6089`, `e2e/tests/web-smoke.spec.mjs:6090`, `e2e/tests/web-smoke.spec.mjs:6091`, `e2e/tests/web-smoke.spec.mjs:6093`, `e2e/tests/web-smoke.spec.mjs:6094`, `e2e/tests/web-smoke.spec.mjs:6095`, `e2e/tests/web-smoke.spec.mjs:6096`, `e2e/tests/web-smoke.spec.mjs:6098`, `e2e/tests/web-smoke.spec.mjs:6099`, `e2e/tests/web-smoke.spec.mjs:6101`에서 `보조 커뮤니티`, `brunch` 미노출과 `기사 교차 확인`, `보조 기사`, `hankyung.com`, `mk.co.kr` 유지를 직접 검증합니다. docs `README.md:180`, `README.md:181`, `docs/MILESTONES.md:95`, `docs/ACCEPTANCE_CRITERIA.md:1389`, `docs/ACCEPTANCE_CRITERIA.md:1390`, `docs/TASK_BACKLOG.md:87`, `docs/TASK_BACKLOG.md:88`도 이미 same truth를 고정합니다. follow-up과 second-follow-up이 같은 negative/positive contract를 공유하므로, 이 둘을 한 coherent slice로 닫는 편이 더 truthful합니다.

## 검증
- `sed -n '1,220p' .agents/skills/round-handoff/SKILL.md`
- `sed -n '1,220p' work/README.md`
- `sed -n '1,220p' verify/README.md`
- `sed -n '1,220p' .pipeline/README.md`
- `sed -n '1,240p' work/4/8/2026-04-08-latest-update-news-only-natural-reload-browser-anchor-source-path-exact-field-wording-clarification.md`
- `sed -n '1,240p' verify/4/8/2026-04-08-latest-update-single-source-natural-reload-browser-anchor-source-path-exact-field-wording-clarification-verification.md`
- `sed -n '1,220p' .pipeline/claude_handoff.md`
- `git status --short`
- `git diff -- e2e/tests/web-smoke.spec.mjs`
- `git diff --check -- e2e/tests/web-smoke.spec.mjs`
- `rg -c '^test\(' e2e/tests/web-smoke.spec.mjs`
- `nl -ba e2e/tests/web-smoke.spec.mjs | sed -n '5510,5569p'`
- `nl -ba e2e/tests/web-smoke.spec.mjs | sed -n '5828,5894p'`
- `nl -ba e2e/tests/web-smoke.spec.mjs | sed -n '5894,5962p'`
- `nl -ba e2e/tests/web-smoke.spec.mjs | sed -n '5960,6075p'`
- `nl -ba e2e/tests/web-smoke.spec.mjs | sed -n '6034,6105p'`
- `nl -ba README.md | sed -n '170,180p'`
- `nl -ba README.md | sed -n '178,183p'`
- `nl -ba docs/MILESTONES.md | sed -n '89,95p'`
- `nl -ba docs/MILESTONES.md | sed -n '94,97p'`
- `nl -ba docs/ACCEPTANCE_CRITERIA.md | sed -n '1381,1389p'`
- `nl -ba docs/ACCEPTANCE_CRITERIA.md | sed -n '1387,1391p'`
- `nl -ba docs/TASK_BACKLOG.md | sed -n '79,87p'`
- `nl -ba docs/TASK_BACKLOG.md | sed -n '85,89p'`
- `cd e2e && npx playwright test tests/web-smoke.spec.mjs -g "latest-update news-only 자연어 reload" --reporter=line`
- `python3 -m unittest -v`, `make e2e-test`는 이번 wording verification 범위를 넘어가므로 재실행하지 않았습니다.

## 남은 리스크
- `e2e/tests/web-smoke.spec.mjs:5965`, `e2e/tests/web-smoke.spec.mjs:6034`의 latest-update noisy-community natural-reload title 2개는 아직 generic wording입니다. 현재 body와 문서는 이미 `보조 커뮤니티`, `brunch` negative assertion과 `기사 교차 확인`, `보조 기사`, `hankyung.com`, `mk.co.kr` positive retention을 직접 고정하므로, 다음 라운드에서 title wording만 맞추는 것이 가장 작은 same-family current-risk reduction입니다.
- history-card latest-update noisy-community click-reload follow-up/second-follow-up family는 이번 verification 범위 밖이라 재판정하지 않았습니다.
