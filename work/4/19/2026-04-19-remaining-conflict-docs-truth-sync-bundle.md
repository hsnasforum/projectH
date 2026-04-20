# 2026-04-19 remaining conflict docs truth sync bundle

## 변경 파일
- docs/ARCHITECTURE.md
- docs/PRODUCT_PROPOSAL.md
- docs/project-brief.md
- docs/TASK_BACKLOG.md

## 사용 skill
- doc-sync: 이미 shipped된 CONFLICT focus-slot explanation wording에 맞춰 네 개의 잔여 문서 문장만 동기화하고, current contract 밖으로 범위를 넓히지 않았습니다.
- work-log-closeout: `/work` 표준 섹션 순서로 실제 변경 파일, 실제 검증, 남은 리스크만 정리했습니다.

## 변경 이유
- seq 385에서 구현된 focus-slot `정보 상충` 상태가 `docs/ACCEPTANCE_CRITERIA.md`와 `docs/PRODUCT_SPEC.md`에는 이미 반영됐지만, `docs/ARCHITECTURE.md`, `docs/PRODUCT_PROPOSAL.md`, `docs/project-brief.md`, `docs/TASK_BACKLOG.md`에는 여전히 4-state 설명 꼬리가 남아 있었습니다.
- 이번 handoff는 same-family docs-only round 3의 마지막 bounded bundle로, 남은 CONFLICT-family docs drift를 이 한 번에 닫고 더 이상의 당일 docs-only micro-round를 만들지 않는 것이 목표였습니다.

## 핵심 변경
- `docs/ARCHITECTURE.md:11`, `docs/ARCHITECTURE.md:142`, `docs/ARCHITECTURE.md:1377`의 focus-slot reinvestigation explanation 꼬리를 모두 `(reinforced / regressed / still single-source / still unresolved / or remains in an explicit \`정보 상충\` state)`로 확장했습니다.
- `docs/PRODUCT_PROPOSAL.md:26`, `docs/PRODUCT_PROPOSAL.md:65`도 같은 mechanical extension만 적용했고, `:26`의 trailing `already shipped.` 문구는 그대로 보존했습니다.
- `docs/project-brief.md:15`, `docs/project-brief.md:89`도 같은 꼬리 문구만 확장했습니다. 긴 요약 문장 구조, 다른 clause, trailing punctuation은 건드리지 않았습니다.
- `docs/TASK_BACKLOG.md:25` item 11의 focus-slot tail만 같은 형태로 확장했고, 같은 줄 앞쪽의 4-segment fact-strength bar (`교차 확인 / 정보 상충 / 단일 출처 / 미확인`)는 이미 truthful하므로 그대로 두었습니다.
- `docs/TASK_BACKLOG.md:26`의 Playwright scenario 설명과 `docs/TASK_BACKLOG.md:823`의 SQLite parity gate 설명은 모두 intentionally untouched로 두었습니다. 둘 다 historical/implemented coverage list 성격의 문장이라 이번 CONFLICT-family docs-sync bundle 범위를 넘고, 필요하더라도 별도 Playwright-parity-docs round에서 다뤄야 합니다.
- 이번 라운드에서는 위 네 파일 외에는 수정하지 않았습니다. `docs/PRODUCT_SPEC.md`(seq 401에서 종료), `docs/ACCEPTANCE_CRITERIA.md`(seq 381/382에서 종료), `docs/MILESTONES.md`(seq 381), 모든 response-body section-header 3-tag enumeration, code, tests, 다른 markdown 파일은 건드리지 않았고, 네 대상 파일 안의 pre-existing unrelated dirty hunk도 보존했습니다.

## 검증
- `git diff --check -- docs/ARCHITECTURE.md docs/PRODUCT_PROPOSAL.md docs/project-brief.md docs/TASK_BACKLOG.md`
  - 결과: 출력 없음, 통과.
- `grep -nE 'reinforced / regressed / still single-source / still unresolved / or remains in an explicit \`정보 상충\` state' docs/ARCHITECTURE.md docs/PRODUCT_PROPOSAL.md docs/project-brief.md docs/TASK_BACKLOG.md`
  - 결과: target 8문장이 아래 줄번호로 확인됐습니다.
    - `docs/ARCHITECTURE.md:11`
    - `docs/ARCHITECTURE.md:142`
    - `docs/ARCHITECTURE.md:1377`
    - `docs/PRODUCT_PROPOSAL.md:26`
    - `docs/PRODUCT_PROPOSAL.md:65`
    - `docs/project-brief.md:15`
    - `docs/project-brief.md:89`
    - `docs/TASK_BACKLOG.md:25`
- `grep -nE 'reinforced / regressed / still single-source / still unresolved' docs/ARCHITECTURE.md docs/PRODUCT_PROPOSAL.md docs/project-brief.md docs/TASK_BACKLOG.md`
  - 결과: extended 문장도 shared substring 때문에 함께 매치되어 target 8문장과 `docs/TASK_BACKLOG.md:26`이 함께 출력됐습니다. 출력 lead-in을 직접 확인한 결과, 이번 round에서 놓친 pure old-style target sentence는 없었습니다.
  - `docs/TASK_BACKLOG.md:26`은 handoff 지시대로 intentionally untouched 상태로 남았습니다.
  - `docs/TASK_BACKLOG.md:823`도 intentionally untouched로 유지했지만, 현재 tree에서는 exact old-style 4-state literal이 아니라 더 긴 historical parity wording이라 이 grep에는 걸리지 않았습니다.
- 이번 라운드는 docs-only bundle이라 code test와 Playwright rerun은 실행하지 않았습니다. `tests.test_web_app`, `tests.test_smoke`, Playwright, `make e2e-test`는 모두 범위 밖이었고, 검증 체크로는 `git diff --check`와 두 scoped `grep`만 사용했습니다.

## 남은 리스크
- same-day same-family docs-only round count는 이제 3으로 `3+ docs-only same-family` guard edge에 도달했습니다. 오늘은 더 이상의 CONFLICT-family docs-only round를 열면 안 됩니다.
- 이번 두 scoped grep과 target-line 재확인 기준으로, 이번 패턴의 다른 CONFLICT-family stale sentence가 네 대상 파일 안에 추가로 slipped-through 하지는 않았습니다.
- `docs/TASK_BACKLOG.md:26`과 `docs/TASK_BACKLOG.md:823`은 intentionally untouched 상태로 남아 있습니다. 둘 다 Playwright/history-parity 설명 축이라 필요 시 별도 Playwright-parity-docs round에서만 다루는 편이 맞습니다.
- Milestone 4의 remaining code sub-axis인 COMMUNITY/PORTAL/BLOG weighting, strong-vs-weak-vs-unresolved separation beyond CONFLICT, response-body `[정보 상충]` tag emission, 추가 reinvestigation tuning은 separate future code round 후보로 남습니다.
- unrelated full `python3 -m unittest tests.test_web_app` failure family는 이번 handoff 범위 밖으로 그대로 남아 있습니다.
