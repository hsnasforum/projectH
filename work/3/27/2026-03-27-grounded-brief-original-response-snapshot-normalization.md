## 변경 파일
- `core/agent_loop.py`
- `app/web.py`
- `storage/session_store.py`
- `tests/test_smoke.py`
- `tests/test_web_app.py`
- `docs/PRODUCT_SPEC.md`
- `docs/ARCHITECTURE.md`
- `docs/ACCEPTANCE_CRITERIA.md`
- `docs/MILESTONES.md`
- `docs/TASK_BACKLOG.md`
- `docs/NEXT_STEPS.md`
- `work/3/27/2026-03-27-grounded-brief-original-response-snapshot-normalization.md`

## 사용 skill
- `security-gate`
- `doc-sync`
- `release-check`
- `work-log-closeout`

## 변경 이유
- 이전 closeout에서 이어받은 리스크:
  - `artifact_id`는 구현됐지만 grounded-brief original-response snapshot contract는 아직 정규화되지 않았음
  - assistant message가 raw snapshot surface라는 문서 약속과 response/session serialization shape가 아직 코드로 고정되지 않았음
  - legacy grounded-brief message를 같은 snapshot contract로 읽을 방법이 없었음
- 이번 라운드에서 해소한 리스크:
  - original grounded-brief assistant message에 nested `original_response_snapshot`을 실제로 추가함
  - response/session serialization에서 같은 snapshot contract를 노출하도록 맞춤
  - approval / task-log는 full snapshot dump 없이 `artifact_id` anchor만 따라가도록 유지함
  - legacy grounded-brief message도 session load 시 같은 snapshot shape로 backfill 가능하게 함
- 여전히 남은 리스크:
  - corrected outcome persistence는 아직 없음
  - separate artifact store와 review queue는 아직 없음
  - `assistant_message_id`를 별도 artifact record로 분리하는 단계는 아직 future work임

## 핵심 변경
- `core/agent_loop.py`
  - grounded-brief 원문 응답만 `self._build_grounded_brief_response(...)`를 통해 생성하도록 정리함
  - `AgentResponse`에 optional `original_response_snapshot` 필드를 추가함
  - snapshot shape는 nested object로 고정함:
    - `artifact_id`
    - `artifact_kind`
    - `draft_text`
    - `source_paths`
    - `response_origin`
    - `summary_chunks_snapshot`
    - `evidence_snapshot`
  - approval granted / rejected / reissued 같은 후속 시스템 응답은 snapshot을 만들지 않고 anchor만 유지함
- `storage/session_store.py`
  - grounded-brief assistant message의 raw fields에서 normalized snapshot을 derive/refresh하는 경로를 추가함
  - legacy message가 `artifact_id`와 evidence/summary chunk를 이미 갖고 있으면 session load 시 snapshot을 backfill하도록 함
  - schema version bump 없이 additive optional field로 유지함
- `app/web.py`
  - response origin이 최종 확정된 뒤 snapshot의 `response_origin`도 같이 동기화하도록 함
  - response payload와 session payload에서 `original_response_snapshot`을 같은 shape로 직렬화함
  - approval payload와 task-log는 기존처럼 anchor-only로 유지하고 full snapshot은 복사하지 않음
- 테스트
  - grounded-brief response와 persisted assistant message가 같은 snapshot contract를 갖는지 회귀를 추가함
  - legacy grounded-brief message가 session payload에서 snapshot으로 backfill되는지 테스트를 추가함
  - approval execute 후 시스템 응답이 snapshot을 복사하지 않는지 확인함
- 문서
  - current shipped behavior와 future corrected outcome / review queue / user-level memory를 다시 분리해 동기화함

## 검증
- 실행함:
  - `python3 -m py_compile core/agent_loop.py app/web.py storage/session_store.py tests/test_smoke.py tests/test_web_app.py`
  - `python3 -m unittest -v tests.test_smoke tests.test_web_app`
  - `git diff --check`
  - `git diff --check -- core/agent_loop.py app/web.py storage/session_store.py tests/test_smoke.py tests/test_web_app.py docs/PRODUCT_SPEC.md docs/ARCHITECTURE.md docs/ACCEPTANCE_CRITERIA.md docs/MILESTONES.md docs/TASK_BACKLOG.md docs/NEXT_STEPS.md`
  - `rg -n "original_response_snapshot|artifact_id|artifact_kind|draft_text|summary_chunks_snapshot|evidence_snapshot" core/agent_loop.py app/web.py storage/session_store.py tests/test_smoke.py tests/test_web_app.py docs/PRODUCT_SPEC.md docs/ARCHITECTURE.md docs/ACCEPTANCE_CRITERIA.md docs/MILESTONES.md docs/TASK_BACKLOG.md docs/NEXT_STEPS.md`

## 남은 리스크
- 이전 closeout에서 이어받은 리스크 중 `original-response snapshot normalization 부재`는 해소했습니다.
- 이번 라운드에서 해소하지 않은 리스크:
  - corrected outcome의 최소 persistence contract
  - normalized snapshot 위에 eval-ready core chain을 완성하는 다음 slice
  - separate artifact record 없이 언제까지 current message/session surface로 버틸지
- 다음 slice 후보:
  - `artifact_id`와 `message_id`를 재사용하는 corrected outcome linkage
  - corrected outcome과 current snapshot contract를 잇는 최소 acceptance / eval regression
