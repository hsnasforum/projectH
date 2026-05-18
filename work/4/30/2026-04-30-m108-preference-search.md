# 2026-04-30 M108 preference search visibility parity

## 변경 파일

- `app/frontend/src/components/PreferencePanel.tsx`
- `work/4/30/2026-04-30-m108-preference-search.md`

## 사용 skill

- `e2e-smoke-triage`: UI selector 추가에 따른 browser-contract 리스크 확인
- `finalize-lite`: 구현 후 검증 범위와 closeout 준비 확인
- `work-log-closeout`: 변경 파일, 실행 검증, 잔여 리스크 기록

## 변경 이유

- `.pipeline/implement_handoff.md` CONTROL_SEQ 1481의 `m108_axis1_preference_search_visibility_parity` 실행.
- 교정 기록 패널에는 검색 입력이 있지만 선호 목록에는 동일한 가시성/탐색 수단이 없어, 선호 리뷰 목록에서도 텍스트 기반 검색이 가능해야 했다.

## 핵심 변경

- `PreferencePanel` 선호 목록에 `data-testid="preference-search-input"` 검색 입력을 추가했다.
- 기존 상태 탭 필터를 먼저 적용한 뒤, 검색어가 있으면 클라이언트에서 선호 항목을 추가 필터링하도록 했다.
- 검색 대상은 `description`, `corrected_text`, `corrected_snippet`, `original_snippet`, `status`다.
- 빈 검색어는 기존처럼 전체 결과를 유지하고, 검색어가 있을 때 결과가 없으면 `검색 결과가 없습니다`를 표시한다.
- 서버/API/Python 경로는 변경하지 않았다.

## 검증

- `app/frontend/node_modules/.bin/tsc --noEmit -p app/frontend/tsconfig.json` 통과.
- `grep -n "preference-search-input" app/frontend/src/components/PreferencePanel.tsx` 확인: `815:data-testid="preference-search-input"`.
- `git diff --check -- app/frontend/src/components/PreferencePanel.tsx` 통과.
- Python 파일 변경이 없어 `python3 -m py_compile`은 실행하지 않았다.
- 클라이언트 전용 필터 구현이라 신규 서버 테스트는 추가하지 않았다.

## 남은 리스크

- handoff가 code-only / no dist rebuild 범위라 `app/static/dist` 재빌드는 실행하지 않았다.
- Playwright는 실행하지 않았다. 새 selector와 브라우저 흐름 검증은 후속 dist/E2E 또는 CI에서 확인해야 한다.
- 문서 동기화는 이번 handoff 범위 밖이며, 현재 docs-only 반복 제한/후속 triage 맥락 때문에 수행하지 않았다.
- commit, push, branch/PR publish, next-slice 선택은 수행하지 않았다.
