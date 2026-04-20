# 2026-04-19 product spec conflict docs truth sync

## 변경 파일
- docs/PRODUCT_SPEC.md

## 사용 skill
- work-log-closeout: `/work` 표준 섹션 순서에 맞춰 이번 docs-only truth-sync 라운드의 실제 변경, 실제 검증, 남은 리스크만 기록했습니다.

## 변경 이유
- seq 382/385/400 이후 `docs/PRODUCT_SPEC.md` 안의 CONFLICT-family 설명 6문장이 현재 shipped contract와 어긋났고, verify가 같은 파일 안의 stale 문장을 한 번에 닫는 bounded bundle을 다음 implement slice로 지정했습니다.
- 이번 handoff는 `docs/PRODUCT_SPEC.md` 한 파일만 대상으로 하는 docs-only sync였고, 같은 파일에 이미 있던 unrelated dirty hunk는 보존한 채 지정된 6문장만 맞추는 것이 핵심이었습니다.

## 핵심 변경
- `docs/PRODUCT_SPEC.md:107`을 `[교차 확인]`, `[정보 상충]`, `[단일 출처]`, `[미확인]` 순서의 panel status tags와 `or remains in an explicit \`정보 상충\` state` tail이 들어간 focus-slot explanation으로 갱신했습니다.
- `docs/PRODUCT_SPEC.md:155`는 bracket-tag 열거는 건드리지 않고, focus-slot reinvestigation explanation 목록만 `or remains in an explicit \`정보 상충\` state`까지 확장했습니다.
- `docs/PRODUCT_SPEC.md:344`는 claim verification / coverage panel의 leading status tags를 `[교차 확인]`, `[정보 상충]`, `[단일 출처]`, `[미확인]` 4개로 맞췄고, `docs/PRODUCT_SPEC.md:348`은 focus-slot plain-language explanation 문장을 `정보 상충` explicit state까지 확장했습니다.
- `docs/PRODUCT_SPEC.md:367`은 panel 4-tag + focus-slot `정보 상충` tail을 함께 반영했고, `docs/PRODUCT_SPEC.md:369`는 reinvestigation suggestion baseline을 `weak/missing/conflict slots all eligible ... MISSING preferred over WEAK and CONFLICT below both`로 바꿔 seq 400 구현과 맞췄습니다.
- `docs/PRODUCT_SPEC.md:347`는 response-body 3-tag enumeration이 `docs/ACCEPTANCE_CRITERIA.md:49`의 현재 emitted-tag 계약과 여전히 일치하므로 의도적으로 수정하지 않았고, `docs/PRODUCT_SPEC.md:370`도 response-body 3-tag surface가 아직 truthful하므로 유지했으며, `docs/PRODUCT_SPEC.md:269`의 `claim_coverage_summary` 4-key shape도 이미 truthful해서 건드리지 않았습니다.
- 이번 라운드에서는 `docs/PRODUCT_SPEC.md` 외 다른 파일을 수정하지 않았습니다. code, tests, other markdown, `CLAUDE.md`, `AGENTS.md`, `GEMINI.md`, `README.md`, `PROJECT_CUSTOM_INSTRUCTIONS.md`, `docs/ACCEPTANCE_CRITERIA.md`, `docs/ARCHITECTURE.md`, `docs/MILESTONES.md`, `docs/TASK_BACKLOG.md`, `docs/PRODUCT_PROPOSAL.md`, `docs/project-brief.md`는 모두 untouched로 두었고, `docs/PRODUCT_SPEC.md` 안의 pre-existing unrelated dirty hunk도 보존했습니다.

## 검증
- `git diff --check -- docs/PRODUCT_SPEC.md`
  - 결과: 출력 없음, 통과.
- `grep -nE "정보 상충|\[교차 확인\]|\[정보 상충\]|\[단일 출처\]|\[미확인\]|conflict|reinforced|regressed|still single-source|still unresolved|weak/missing" docs/PRODUCT_SPEC.md`
  - 결과: target 문장 6개가 아래 줄번호/lead-in text로 확인됐습니다.
    - `107:- claim coverage panel with status tags (\`[교차 확인]\`, \`[정보 상충]\`, \`[단일 출처]\`, \`[미확인]\`), ... (reinforced / regressed / still single-source / still unresolved / or remains in an explicit \`정보 상충\` state) ...`
    - `155:- supports entity-card and latest-update answer-mode distinction ... explanation covering reinforced / regressed / still single-source / still unresolved / or remains in an explicit \`정보 상충\` state ...`
    - `344:- claim verification / coverage panel where applicable, with status tags (\`[교차 확인]\`, \`[정보 상충]\`, \`[단일 출처]\`, \`[미확인]\`) ...`
    - `348:- slot-level reinvestigation UX ... telling the user whether the slot was reinforced, regressed, is still single-source, is still unresolved, or remains in an explicit \`정보 상충\` state ...`
    - `367:- claim coverage panel with status tags (\`[교차 확인]\`, \`[정보 상충]\`, \`[단일 출처]\`, \`[미확인]\`), ... (reinforced / regressed / still single-source / still unresolved / or remains in an explicit \`정보 상충\` state)`
    - `369:- weak-slot reinvestigation baseline: weak/missing/conflict slots all eligible for reinvestigation suggestions, with MISSING preferred over WEAK and CONFLICT below both, ...`
  - 같은 grep 검토에서 `docs/PRODUCT_SPEC.md:347`, `:370`, `:269`가 의도한 untouched 상태로 남아 있음을 함께 확인했습니다.
- 이번 라운드는 `docs/PRODUCT_SPEC.md` 한 파일만 건드린 docs-only truth-sync라서 code test와 Playwright rerun은 실행하지 않았습니다. `tests.test_web_app`, `tests.test_smoke`, Playwright, `make e2e-test`는 모두 범위 밖이었고, 실제로 실행한 체크는 `git diff --check`와 scoped `grep` 두 개뿐입니다.

## 남은 리스크
- parallel stale sentence는 여전히 `docs/ARCHITECTURE.md:11/142/1377`, `docs/PRODUCT_PROPOSAL.md:26/65`, `docs/project-brief.md:15/89`, `docs/TASK_BACKLOG.md:25` focus-slot tail에 남아 있습니다. 이들은 separate bounded docs-sync bundle 후보로 남기며, 그 라운드는 same-family docs-only round 3이 되므로 더 쪼개지 말고 한 번에 닫는 편이 맞습니다.
- Milestone 4의 remaining code sub-axis인 COMMUNITY/PORTAL/BLOG weighting, strong-vs-weak-vs-unresolved separation beyond CONFLICT, response-body `[정보 상충]` tag emission, 추가 reinvestigation tuning은 이번 docs-only slice 밖의 future code round 후보입니다.
- unrelated full `python3 -m unittest tests.test_web_app` failure family도 이번 handoff 범위 밖으로 그대로 남아 있습니다.
