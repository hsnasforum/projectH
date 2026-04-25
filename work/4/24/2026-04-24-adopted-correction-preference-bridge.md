# 2026-04-24 adopted correction preference bridge

## 변경 파일
- `app/handlers/preferences.py`
- `app/web.py`
- `tests/test_preference_handler.py`
- `work/4/24/2026-04-24-adopted-correction-preference-bridge.md`

## 사용 skill
- `security-gate`: ACTIVE correction을 local preference candidate로 쓰는 POST 경로라서 local-first, 승인/활성화 경계, task log 기록 여부를 확인했습니다.
- `finalize-lite`: handoff 범위, 실제 실행 검증, 문서 동기화 필요 여부를 좁게 점검했습니다.
- `work-log-closeout`: 실제 변경 파일과 실행한 검증만 한국어 `/work` 기록으로 남겼습니다.

## 변경 이유
- M29 Axis 1 handoff가 채택된 correction(`status=ACTIVE`)을 preference candidate로 동기화하는 bridge를 요구했습니다.
- 기존 `find_adopted_corrections()`와 `record_reviewed_candidate_preference()` 저장소 API는 있었지만, adopted correction 목록을 reviewable preference candidate로 연결하는 handler/API 경로가 없었습니다.

## 핵심 변경
- `PreferenceHandlerMixin.sync_adopted_corrections_to_candidates()`를 추가해 adopted correction을 순회하고, 기존 preference fingerprint가 있으면 건너뛰도록 했습니다.
- 새 candidate는 `delta_fingerprint`, `pattern_family`, `delta_summary` 또는 `corrected_text` 기반 description, correction source refs, 원문/수정 snippet을 기존 `record_reviewed_candidate_preference()`에 전달해 생성합니다.
- JSON preference store의 `find_by_fingerprint()`를 우선 사용하고, SQLite preference store처럼 직접 조회 메서드가 없는 경우 `list_all()` 기반 fallback으로 중복 조회를 수행했습니다.
- `POST /api/corrections/sync-adopted-to-candidates`를 `app/web.py`에 등록했고, 요청 본문 없이 same-origin 검증 후 실행되도록 했습니다.
- sync 실행 결과를 `synced_count` / `skipped_count`로 반환하고, 가능하면 `adopted_corrections_synced_to_candidates` task log를 남기도록 했습니다.
- `tests/test_preference_handler.py`에 mapping, existing fingerprint skip, empty adopted list 단위 테스트를 추가했습니다.

## 검증
- `python3 -m py_compile app/handlers/preferences.py app/web.py`
  - 통과: 출력 없음
- `python3 -m unittest tests.test_preference_handler`
  - 통과: 11개 테스트 OK
- `rg -n "sync-adopted-to-candidates|sync_adopted_corrections_to_candidates" app/web.py app/handlers/preferences.py tests/test_preference_handler.py`
  - 통과: handler method, POST route, 단위 테스트 위치를 확인했습니다.
- `git diff --check`
  - 통과: 출력 없음

## 남은 리스크
- handoff의 컴파일 예시는 `web_app.py`를 언급했지만, 이 repo의 실제 HTTP 소유자는 `app/web.py`이고 루트 `web_app.py`는 없어 `app/web.py`로 검증했습니다.
- 이번 bridge는 preference candidate 생성까지만 수행하며, preference 활성화나 UI 노출 변경은 하지 않았습니다.
- 문서, frontend/UI, storage 구현 파일, pipeline control slot은 handoff 범위 밖이라 수정하지 않았습니다.
- 작업 전부터 존재하던 `docs/MILESTONES.md`, `report/gemini/2026-04-24-m29-direction.md`, `verify/4/24/2026-04-24-m28-milestones-doc-sync.md`, 이전 `/work` untracked 파일들은 이번 round에서 변경하지 않았습니다.
- commit, push, branch/PR publish, next-slice 선택, `.pipeline/advisory_request.md`, `.pipeline/operator_request.md` 작성은 수행하지 않았습니다.
