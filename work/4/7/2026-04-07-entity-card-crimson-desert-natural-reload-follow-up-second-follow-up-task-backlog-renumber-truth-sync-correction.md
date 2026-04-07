# entity-card crimson-desert natural-reload follow-up/second-follow-up task-backlog renumber truth-sync correction

날짜: 2026-04-07

## 변경 파일
- `docs/TASK_BACKLOG.md`

## 사용 skill
- 없음 (docs-only numbering correction)

## 변경 이유
- 이전 라운드에서 TASK_BACKLOG.md에 2개 noisy-exclusion entry를 삽입한 뒤 후속 번호 재정렬 시 55, 56이 빠지고 57, 58이 중복되는 numbering 오류가 있었습니다.
- 구체적으로: 54 다음이 57(→55), 58(→56)이었고, 그 뒤 57, 58이 다시 나타나는 상태였습니다.

## 핵심 변경
- line 68: `57.` → `55.` (second-follow-up noisy exclusion entry)
- line 69: `58.` → `56.` (history-card actual-search entry)
- 후속 57, 58, 59... 는 이미 정확하여 수정 불필요
- 결과: 53, 54, 55, 56, 57, 58, 59, 60... 단조 증가 확인

## 검증
- `git diff --check -- docs/TASK_BACKLOG.md`: clean
- 53~62 범위 단조 증가 확인 완료

## 남은 리스크
- 없음 (numbering-only correction)
