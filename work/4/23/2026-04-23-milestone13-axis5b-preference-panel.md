# 2026-04-23 Milestone 13 Axis 5b preference panel

## 변경 파일
- `app/frontend/src/api/client.ts`
- `app/frontend/src/components/PreferencePanel.tsx`
- `work/4/23/2026-04-23-milestone13-axis5b-preference-panel.md`

## 사용 skill
- `finalize-lite`: frontend 변경 후 실행한 검증, 미실행 검증, doc-sync 필요 여부를 마무리 확인.
- `work-log-closeout`: 이번 구현 라운드의 변경 파일, 검증, 남은 리스크를 한국어 `/work` 노트로 기록.

## 변경 이유
- M13 Axis 5 backend는 `/api/preferences`의 각 preference record에 `reliability_stats.applied_count`와 `reliability_stats.corrected_count`를 포함한다.
- 기존 `PreferencePanel.tsx`는 선호 상태, 설명, 증거 수, action만 보여 주고 reliability stats를 노출하지 않았다.
- 사용자가 선호가 실제 응답에 얼마나 반영됐고, 반영 후 교정이 얼마나 발생했는지 sidebar에서 바로 볼 수 있어야 한다.

## 핵심 변경
- `PreferenceRecord` 타입에 optional/null-safe `reliability_stats` 필드를 추가했다.
- `PreferencePanel.tsx`에 `preferenceReliabilityCounts()` helper를 추가해 missing/null/non-finite count를 0으로 처리한다.
- 각 preference card의 설명 아래에 작은 muted 라벨 `적용 N회 · 교정 M회`를 표시한다.
- 기존 status label, description, delta summary, active/pause/reject action 표시 흐름은 유지했다.
- backend, storage, pipeline runtime, control slot 파일은 수정하지 않았다.

## 검증
- `sha256sum .pipeline/implement_handoff.md` → 요청된 handoff SHA `e61386eeb8105ecefbc0497d33c0e421982e5438ff94a8a56ece849f8b3cb58f`와 일치.
- `npm --prefix app/frontend exec tsc -- --noEmit` → npm exec 인자 전달 문제로 `tsc` help만 출력되어 유효 검증으로 보지 않음.
- `npm --prefix app/frontend exec tsc --noEmit` → 동일하게 `tsc` help만 출력되어 유효 검증으로 보지 않음.
- `./node_modules/.bin/tsc --noEmit` (`workdir=app/frontend`) → 통과.
- `git diff --check -- app/frontend/src/api/client.ts app/frontend/src/components/PreferencePanel.tsx` → 통과.
- `git diff -- app/frontend/src/api/client.ts app/frontend/src/components/PreferencePanel.tsx` → diff 확인 완료.

## 남은 리스크
- 실제 브라우저 UI screenshot이나 Playwright는 실행하지 않았다. 이번 slice는 기존 component의 타입/렌더링 보강이며 handoff acceptance가 frontend 표시와 null-safe 처리에 한정되어 있어 `tsc --noEmit` 중심으로 확인했다.
- `verify/4/23/2026-04-23-milestone12-axis3-trace-quality-scoring.md`는 이번 라운드 전부터 dirty 상태였고 수정하지 않았다. 커밋 범위 정리 시 별도 판단이 필요하다.
