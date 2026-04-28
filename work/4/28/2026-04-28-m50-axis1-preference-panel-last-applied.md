# 2026-04-28 M50 Axis 1 PreferencePanel 이번 응답 반영 표시

## 변경 파일

- `app/frontend/src/App.tsx`
- `app/frontend/src/components/Sidebar.tsx`
- `app/frontend/src/components/PreferencePanel.tsx`
- `docs/MILESTONES.md`
- `work/4/28/2026-04-28-m50-axis1-preference-panel-last-applied.md`

## 사용 skill

- `doc-sync`: 구현 사실을 `docs/MILESTONES.md`의 M50 항목에 제한적으로 반영.
- `work-log-closeout`: 구현 종료 기록을 표준 `/work` 형식으로 작성.

## 변경 이유

- M49에서 summary/chat 응답에 주입된 `applied_preferences`가 message bubble에는 보이지만, 사이드바의 전역 `PreferencePanel`에서는 마지막 응답에 반영된 선호를 구분할 수 없었다.
- 이번 슬라이스는 백엔드, approval, storage를 건드리지 않고 마지막 assistant 응답의 fingerprint만 프론트엔드 prop으로 전달해 카드 배지를 표시한다.

## 핵심 변경

- `App.tsx`에서 `chat.messages`를 역순으로 훑어 마지막 assistant 메시지의 `applied_preferences[].fingerprint` 목록을 계산했다.
- `Sidebar.tsx`에 `lastAppliedFingerprints` optional prop을 추가하고 `PreferencePanel`로 전달했다.
- `PreferencePanel.tsx`에서 전달받은 fingerprint `Set`을 만들고, `active` 상태 선호 카드의 `delta_fingerprint`가 포함될 때만 `data-testid="preference-last-applied-badge"` 배지를 표시했다.
- 카드 상단 badge row에 `flex-wrap`을 추가해 기존 status, 품질, 신뢰도, 충돌 badge와 함께 좁은 사이드바에서 줄바꿈될 수 있게 했다.
- `docs/MILESTONES.md`에 M50 Axis 1 shipped 내용을 추가하고 dist 재빌드는 다음 슬라이스 대상임을 명시했다.

## 검증

- `python3 -m py_compile app/frontend/src/App.tsx 2>/dev/null || npx tsc --noEmit --project app/frontend/tsconfig.json`
  - 실패: root 기준 `npx tsc`가 로컬 바이너리를 잡지 못하고 `https://registry.npmjs.org/tsc` 조회로 빠져 네트워크 제한 `EAI_AGAIN` 발생.
- `app/frontend/node_modules/.bin/tsc --noEmit --project app/frontend/tsconfig.json`
  - 통과.
- `python3 -m py_compile app/serializers.py app/handlers/chat.py`
  - 통과.
- `git diff --check -- app/frontend/src/App.tsx app/frontend/src/components/Sidebar.tsx app/frontend/src/components/PreferencePanel.tsx docs/MILESTONES.md`
  - 통과.

## 남은 리스크

- 핸드오프 non-goal에 따라 `app/static/dist/` 재빌드와 Playwright smoke는 실행하지 않았다.
- 변경은 source TypeScript와 milestone 문서에만 반영되어 있으며, 배포용 dist 반영과 브라우저 확인은 다음 슬라이스에서 별도 검증이 필요하다.
