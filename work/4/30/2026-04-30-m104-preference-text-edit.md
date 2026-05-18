# 2026-04-30 M104 preference text edit

## 변경 파일

- `app/handlers/preferences.py` - `edit_preference_text(preference_id, corrected_text)` handler 추가
- `app/web.py` - `PATCH /api/preferences/<preference_id>` same-origin route 추가
- `app/frontend/src/api/client.ts` - `editPreferenceText()` client 추가 및 `PreferenceRecord.corrected_text` 타입 추가
- `app/frontend/src/components/PreferencePanel.tsx` - `edit-preference-btn`, `save-preference-text-btn` 기반 인라인 교정 텍스트 편집 UI 추가
- `tests/test_web_app.py` - corrected_text 편집 성공/404/빈 텍스트 400 테스트 3개 추가
- `work/4/30/2026-04-30-m104-preference-text-edit.md` - 이번 closeout

## 사용 skill

- `finalize-lite` - 구현 종료 전 실행 사실, 미실행 범위, 문서 동기화 필요 여부를 점검하기 위해 사용
- `work-log-closeout` - `/work` closeout 필수 섹션과 실제 검증/잔여 리스크 기록 형식을 맞추기 위해 사용

## 변경 이유

- `.pipeline/implement_handoff.md` CONTROL_SEQ 1464가 M104 Axis 1 preference corrected_text edit 구현을 지시했다.
- M102 preference delete와 M103 reliability toggle 이후, 남은 preference 수정 축인 corrected_text 편집을 코드-only 범위로 추가했다.

## 핵심 변경

- backend handler가 공백 전용 corrected_text를 400으로 거부하고, unknown preference id를 404로 반환한다.
- `preference_store.update(preference_id, {"corrected_text": ...})`를 재사용해 기존 저장소 update helper 위에 텍스트 편집을 구현했다.
- task log에 `preference_text_edited` action과 `previous_corrected_text`를 기록한다. 기존 record에 `corrected_text`가 없으면 `corrected_snippet`을 이전 값으로 사용한다.
- `PATCH /api/preferences/<preference_id>` route가 JSON body의 `corrected_text`를 handler로 전달한다.
- PreferencePanel은 `corrected_text ?? corrected_snippet`을 현재 교정 텍스트로 표시하고, `edit-preference-btn` 클릭 시 textarea 편집 모드로 전환한다.
- 저장 버튼 `save-preference-text-btn`은 공백 입력에서 비활성화되며, 저장 성공 후 카드 상태를 갱신한다.

## 검증

- `sha256sum .pipeline/implement_handoff.md` - PASS, `f183167de63e4e45f98f6bdc90b87302c6b435e442f959a3e02ad9bc4fa041ac`
- `python3 -m py_compile app/handlers/preferences.py app/web.py` - PASS
- `python3 -m unittest -v tests.test_web_app.WebAppServiceTest.test_edit_preference_text_updates_corrected_text tests.test_web_app.WebAppServiceTest.test_edit_preference_text_returns_404_for_unknown_id tests.test_web_app.WebAppServiceTest.test_edit_preference_text_rejects_empty_text` - PASS, 3 tests
- `app/frontend/node_modules/.bin/tsc --noEmit -p app/frontend/tsconfig.json` - PASS
- `git diff --check -- app/handlers/preferences.py app/web.py app/frontend/src/api/client.ts app/frontend/src/components/PreferencePanel.tsx tests/test_web_app.py` - PASS
- `rg -n "edit_preference_text|PATCH|editPreferenceText|edit-preference-btn|save-preference-text-btn|test_edit_preference_text" app/handlers/preferences.py app/web.py app/frontend/src/api/client.ts app/frontend/src/components/PreferencePanel.tsx tests/test_web_app.py` - PASS

## 남은 리스크

- dist rebuild는 handoff가 제외했으므로 `app/static/dist/assets/`에는 M104 text edit UI가 아직 반영되지 않았다.
- browser/E2E는 이번 Axis 1 code-only handoff 검증 목록에 없어서 실행하지 않았다.
- product docs는 이번 handoff 범위 밖이라 갱신하지 않았다. corrected_text 명시 편집 동작은 후속 doc-sync가 필요하다.
- commit, push, branch/PR publish는 implement role 제약에 따라 수행하지 않았다.
