# 2026-05-22 live Claude verify trigger 9

## 변경 파일
- `work/5/22/2026-05-22-live-claude-verify-trigger-9.md`

## 사용 skill
- `work-log-closeout`: 실제 변경 파일, 실행한 검증, 미실행 범위, 남은 리스크를 한국어 `/work` 기록으로 남기기 위해 사용했습니다.

## 변경 이유
- CONTROL_SEQ 2151에 따라 trigger-9는 900초 verify done deadline 아래에서 Claude verify lane `TASK_DONE source=wrapper lane=Claude`를 관찰하기 위한 metadata-only trigger입니다.
- trigger-8 live run은 `TASK_DONE`이 `TASK_ACCEPTED` 이후 약 7분 3초에 발생해 `finish_stream()` / `claude_result` 경로가 정상임을 확인했지만, 기존 300초 deadline이 먼저 만료됐습니다.
- 900초 deadline은 관찰된 처리 시간보다 충분한 여유를 주므로 trigger-9가 A3 Step 6 진입 여부를 판정하는 관찰 대상입니다.

## 핵심 변경
- 지정된 `/work` trigger note 1개만 새로 추가했습니다.
- `verify/5/22/2026-05-22-live-claude-verify-trigger-9.md`는 생성하지 않았습니다.
- 소스 코드, 런타임 코드, 테스트, profile 파일, `.pipeline/` control slot은 변경하지 않았습니다.
- commit, push, branch/PR publish, merge, release, publication은 실행하지 않았습니다.

## 검증
- 통과: `python3 -c "import json; d=json.load(open('.pipeline/config/agent_profile.json')); assert 'Claude' in d['selected_agents']; assert d['role_bindings']['verify']=='Claude'; print('profile OK')"`
  - 결과: `profile OK`
- 통과: `python3 -c "import os; assert not os.path.exists('verify/5/22/2026-05-22-live-claude-verify-trigger-9.md'), 'ERROR: verify note must not exist'; print('no verify note: OK')"`
  - 결과: `no verify note: OK`
- 통과: `git diff --check -- work/5/22/2026-05-22-live-claude-verify-trigger-9.md`
  - 결과: PASS, 출력 없음

## 남은 리스크
- `TASK_DONE source=wrapper lane=Claude`는 trigger-9에서 아직 관찰하지 않았습니다.
- 다음 단계는 trigger-9 `/verify` note가 없는 상태 그대로 파이프라인을 재시작하고, 새 `events.jsonl`에서 `DISPATCH_SEEN`, `TASK_ACCEPTED`, `TASK_DONE`가 모두 `lane=Claude`로 기록되는지 확인하는 것입니다.
- live `TASK_DONE` 관찰 전에는 `verify/5/22/2026-05-22-live-claude-verify-trigger-9.md`를 작성하지 않아야 합니다.
