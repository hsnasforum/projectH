# 검토 후보 action vocabulary docs truth-sync bundle

## 변경 파일

- `docs/NEXT_STEPS.md`
- `docs/PRODUCT_SPEC.md`
- `docs/ACCEPTANCE_CRITERIA.md`
- `docs/MILESTONES.md`
- `docs/TASK_BACKLOG.md`

## 사용 skill

- 없음

## 변경 이유

이전 구현 슬라이스(`review-queue action-vocabulary expansion: reject and defer`)에서 code/UI/test 변경과 함께 `README.md`, `docs/PRODUCT_SPEC.md`, `docs/ACCEPTANCE_CRITERIA.md` 일부를 동기화했으나, 나머지 root docs에 accept-only 서술이 남아 있었습니다. 이 슬라이스는 남은 docs drift를 한 번에 닫는 bounded bundle입니다.

## 핵심 변경

1. **`docs/NEXT_STEPS.md`**: "accept only / no reject / no defer" 블록을 "`accept`/`reject`/`defer` 세 가지 지원" 서술로 교체. "Keep the shipped accept-only review slice narrow" → 현재 shipped vocabulary 반영.
2. **`docs/PRODUCT_SPEC.md`**: minimum shipped record contract의 `review_action = accept` / `review_status = accepted` 고정값을 enum 집합(`∈ { accept, reject, defer }`)으로 교체. "later contract vocabulary" → shipped/later 분리. queue-removal 규칙을 세 action 모두에 적용. "current shipped first implementation slice: accept only" → 세 action 모두 구현됨으로 수정. "edit / reject / defer UI" 미구현 → "edit UI" 미구현으로 축소.
3. **`docs/ACCEPTANCE_CRITERIA.md`**: record contract, shipped/later action 분리, queue-removal 규칙, shipped action-capable slice 블록 모두 동일 패턴으로 수정.
4. **`docs/MILESTONES.md`**: browser smoke 설명에 `검토 수락`/`거절`/`보류` 세 버튼 반영. "accept only" → "accept, reject, defer". "keep edit / reject / defer later" → "keep edit later".
5. **`docs/TASK_BACKLOG.md`**: backlog item 21 제목에서 "accept-only" → "accept/reject/defer". item 45에서 "implement accept only first" → shipped/later 분리.

## 검증

- `grep -ri "accept.only\|accept-only\|no reject\|no defer\|review_action = accept\|review_status = accepted" docs/NEXT_STEPS.md docs/PRODUCT_SPEC.md docs/ACCEPTANCE_CRITERIA.md docs/MILESTONES.md docs/TASK_BACKLOG.md` → no matches
- `git diff --check -- docs/NEXT_STEPS.md docs/PRODUCT_SPEC.md docs/ACCEPTANCE_CRITERIA.md docs/MILESTONES.md docs/TASK_BACKLOG.md` → clean
- pytest / Playwright 재실행 없음 — docs-only 변경이며 이전 라운드에서 코드 검증 완료

## 남은 리스크

- `docs/PRODUCT_SPEC.md`와 `docs/ACCEPTANCE_CRITERIA.md` 깊은 곳에 "accept"가 여전히 단독으로 등장하는 문장이 있으나, 이들은 action 중 하나를 예시로 설명하는 맥락이지 "accept only"를 주장하는 것이 아님.
- `reject`/`defer` 된 candidate에 대한 aggregate 제외 논리는 아직 미구현 — docs에서도 해당 시맨틱은 아직 서술하지 않음.
