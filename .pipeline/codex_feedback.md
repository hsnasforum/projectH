STATUS: implement

다음 슬라이스: `follow-up Q&A answer-shape consistency only`

근거:
- operator가 완전히 새 품질 축 D를 선택
- follow-up Q&A (key_points, action_items, memo) 답변 형태 일관성 개선

구현 범위:
- `model_adapter/ollama.py`의 follow-up intent system prompt / output contract만 조정
- 답변 형태(bullet 수, 구조, 밀도)가 intent 간에 더 일관되도록 최소 조정
- focused regression 추가

범위 제한:
- follow-up Q&A 품질만
- UI, search ranking, summary length, approval, evidence, web investigation, reviewed-memory 금지
- dirty worktree cleanup 금지
- eval gate 개편 금지

operator 결정 기록:
- entity-card weak-claim honesty family → 닫힘
- React frontend → parked
- parallel stress hardening → current shipped 바깥
