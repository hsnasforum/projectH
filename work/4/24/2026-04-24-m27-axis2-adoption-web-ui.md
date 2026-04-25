# 2026-04-24 M27 Axis 2 adoption web UI

## 변경 파일
- `app/handlers/preferences.py`
- `app/frontend/src/api/client.ts`
- `app/frontend/src/components/PreferencePanel.tsx`
- `app/static/dist/assets/index.js`
- `tests/test_preference_handler.py`
- `docs/MILESTONES.md`
- `work/4/24/2026-04-24-m27-axis2-adoption-web-ui.md`

## 사용 skill
- `doc-sync`: `/api/preferences/audit`와 `PreferencePanel`의 현재 shipped 동작을 `docs/MILESTONES.md` M27 Axis 2 항목에 좁게 동기화했습니다.
- `finalize-lite`: 구현 말미에 실제 변경 파일, 실행한 검증, 문서 동기화 범위, 남은 리스크를 함께 점검했습니다.
- `work-log-closeout`: 이번 구현 라운드의 파일, 검증, dirty worktree 분리를 한국어 closeout으로 기록했습니다.

## 변경 이유
- `.pipeline/implement_handoff.md` `CONTROL_SEQ: 110`이 Milestone 27 Axis 2 `m27_axis2_adoption_count_web_ui`를 지시했습니다.
- 근거는 operator retriage `seq 109`의 council convergence Option A이며, PR merge gate는 operator backlog로 유지됩니다.
- M27 Axis 1에서 추가된 `find_adopted_corrections()`가 script audit에는 노출됐지만, 기존 `/api/preferences/audit`와 `PreferencePanel` audit row에는 adopted correction 수가 보이지 않았습니다.

## 핵심 변경
- `get_preference_audit()`가 `self.correction_store.find_adopted_corrections()` 결과 길이를 `adopted_corrections_count`로 반환하게 했습니다.
- `PreferenceAudit` TypeScript 타입에 optional `adopted_corrections_count` 필드를 추가했습니다.
- `PreferencePanel`의 기존 compact audit row에 adopted count가 1건 이상일 때만 `활성 교정 N개`를 표시하게 했습니다.
- `tests/test_preference_handler.py`의 mock service에 `_CorrectionStore` stub을 추가하고, adopted count 0건/1건 반환 테스트를 추가했습니다.
- `cd app/frontend && npx vite build`로 `app/static/dist/assets/index.js`를 재빌드했습니다.
- `docs/MILESTONES.md`에 M27 Axis 2 shipped entry를 추가했습니다.

## 검증
- `python3 -m py_compile app/handlers/preferences.py tests/test_preference_handler.py`
  - 통과: 출력 없음
- `python3 -m unittest -v tests/test_preference_handler.py -k preference_audit 2>&1 | tail -10`
  - 통과: `Ran 3 tests ... OK`
- `cd app/frontend && npx vite build 2>&1 | tail -5`
  - 통과: `../static/dist/assets/index.js   299.22 kB │ gzip: 90.35 kB`, `built in 2.64s`
- `ls -la app/static/dist/assets/index.js`
  - 통과: `Apr 24 10:43` mtime의 `app/static/dist/assets/index.js` 확인
- `git diff --check -- app/handlers/preferences.py app/frontend/src/api/client.ts app/frontend/src/components/PreferencePanel.tsx tests/test_preference_handler.py docs/MILESTONES.md`
  - 통과: 출력 없음

## 남은 리스크
- full unit discover와 browser/e2e suite는 handoff 범위를 넘어 실행하지 않았습니다.
- UI는 Vite build로 TypeScript/build 무결성만 확인했습니다. Playwright browser smoke는 verify lane의 release gate 범위로 남겼습니다.
- 이번 라운드 시작 전부터 `app/web.py`, `config/settings.py`, `pipeline_gui/setup_controller.py`, `pipeline_gui/setup_executor.py`, `scripts/pipeline_runtime_gate.py`, `scripts/promote_assets.py`, `tests/test_pipeline_gui_app.py`, `tests/test_pipeline_runtime_gate.py`, `tests/test_web_app.py`가 dirty 상태였습니다. 이번 라운드는 해당 파일들을 수정하지 않았습니다.
