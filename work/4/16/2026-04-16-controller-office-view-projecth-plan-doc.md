# 2026-04-16 controller Office View projectH 적용 계획 문서 작성

## 변경 파일
- `docs/superpowers/plans/2026-04-16-controller-office-view-projecth-adaptation.md`
- `work/4/16/2026-04-16-controller-office-view-projecth-plan-doc.md`

## 사용 skill
- `mvp-scope` - 외부 레퍼런스 아이디어를 projectH의 현재 internal/operator runtime 범위로 좁혀 계획 문서 구조를 정리했습니다.
- `work-log-closeout` - 오늘자 작업 노트 형식과 closeout 섹션 순서를 repo 규칙에 맞췄습니다.

## 변경 이유
- 사용자는 `office-for-claude-agents` README_EN을 참고해 `controller/index.html`에 projectH 스타일 Office View를 적용하려고 했고, Claude가 바로 집행할 수 있는 bounded plan 문서가 필요했습니다.
- 현재 `controller/index.html`에는 이미 Office View 토글, 3-lane desk scene, sprite/fallback path, HUD, 이벤트 로그, typed command palette가 존재하므로, 신규 착수 문서가 아니라 "현재 baseline을 기준으로 무엇을 다듬고 무엇을 비목표로 둘지"를 정리하는 문서가 더 truthful했습니다.

## 핵심 변경
- `docs/superpowers/plans/2026-04-16-controller-office-view-projecth-adaptation.md` 신규 추가.
- 외부 레퍼런스에서 projectH가 가져올 요소(live office map, approval alert, event/sidebar context, zoom/pan, optional sprite pipeline)와 그대로 복제하지 않을 요소(boss seat, GitHub TASKS sidebar, share link, multi-daemon, layout editor)를 분리했습니다.
- projectH adaptation rules를 명시해 controller를 `3-lane war-room` read-model로 고정하고, release gate 확대나 새 runtime truth path 도입을 비목표로 못박았습니다.
- Claude가 바로 구현할 수 있도록 파일 범위, 단계별 작업, 검증 계획, 문서 동기화 트리거, 첫 구현 슬라이스 순서를 한 문서에 묶었습니다.

## 검증
- `sed -n '1,220p' work/4/16/2026-04-16-reviewed-memory-stored-review-support-sanitize.md`
- `rg --files controller pipeline_gui windows-launchers | sort`
- `sed -n '1,260p' controller/index.html`
- `sed -n '1320,2065p' controller/index.html`
- `sed -n '1,260p' controller/server.py`
- `sed -n '1,220p' docs/projectH_pipeline_runtime_docs/00_문서세트_안내.md`
- `sed -n '1,220p' docs/projectH_pipeline_runtime_docs/03_기술설계_명세서.md`
- `sed -n '1,240p' docs/projectH_pipeline_runtime_docs/05_운영_RUNBOOK.md`
- `git diff --check -- docs/superpowers/plans/2026-04-16-controller-office-view-projecth-adaptation.md work/4/16/2026-04-16-controller-office-view-projecth-plan-doc.md`
- 코드/런타임/테스트 변경은 없어서 Python unit test와 Playwright는 실행하지 않았습니다.

## 남은 리스크
- 계획 문서는 `controller/index.html`의 현재 baseline을 기준으로 작성했지만, 해당 파일이 이미 dirty worktree에 포함되어 있어 실제 구현 라운드에서는 최신 diff를 다시 읽고 충돌 없이 같은 방향으로 접합해야 합니다.
- 현재 문서는 `docs/superpowers/plans/`에만 추가되었습니다. 이후 controller Office View 계약이나 운영 절차가 실제로 바뀌면 `docs/projectH_pipeline_runtime_docs/03_기술설계_명세서.md`, `05_운영_RUNBOOK.md`, 필요시 `README.md`까지 같은 라운드에서 sync해야 합니다.
