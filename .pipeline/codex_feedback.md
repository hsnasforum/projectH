## Claude에게 전달할 지시사항

STATUS: implement

직전 **narrative faithfulness prompt-family regression**은 이번 verify에서 `ready`로 닫혔습니다. 이번 라운드는 test completeness를 더 파지 말고, **이미 구현된 summary source-type boundary를 response quick-meta에 작은 label 1개로 드러내는 user-visible clarity slice**만 구현하세요.

반드시 먼저 읽을 파일:
- `verify/3/31/2026-03-31-narrative-faithfulness-prompt-regression-verification.md`
- `work/3/31/2026-03-31-narrative-faithfulness-prompt-regression.md`
- `AGENTS.md`
- `work/README.md`
- `verify/README.md`
- `.pipeline/README.md`
- `app/templates/index.html`
- `core/agent_loop.py`
- `README.md`
- `docs/PRODUCT_SPEC.md`
- `docs/ACCEPTANCE_CRITERIA.md`
- `CLAUDE.md`

이번 라운드 단일 슬라이스:
- response quick-meta에 summary source-type label 1개를 추가하세요.
- local file / uploaded document summary면 user가 바로 알아볼 수 있게 `문서 요약` 성격의 label을 보여 주세요.
- selected local search-result summary면 user가 바로 알아볼 수 있게 `검색 결과 요약` 성격의 label을 보여 주세요.
- exact copy는 현재 UI 톤에 맞게 조금 다듬어도 되지만, **원문 문서 요약인지 / 선택 검색 결과 종합인지 즉시 구분된다**는 계약은 유지해 주세요.

왜 이 슬라이스가 지금 맞는지:
- latest `/verify`가 이미 지적했듯이, summary source-type split은 docs와 internal regression에는 정직하지만 user-visible UI에는 아직 직접 드러나지 않습니다.
- 이 라운드는 summary behavior를 다시 건드리는 게 아니라, 이미 shipped truth를 사용자에게 얇게 드러내는 작은 clarity 개선입니다.

정확한 범위 제한:
- `app/templates/index.html` 중심으로 해결하는 쪽을 먼저 보세요.
- 현재 payload에 source-type 구분이 없어서 꼭 필요할 때만 `app/web.py`를 최소 범위로 만지세요.
- summary behavior 자체, prompt wording, reviewed-memory, approval flow, investigation UI, unrelated dirty file 정리 금지.
- 새 mode toggle, 설정, classifier, 추가 필터 금지.
- current shipped source-type split을 visible clarity로만 드러내세요.
- UI behavior가 바뀌면 관련 root docs를 같은 라운드에 truth-sync 하세요.
- 최소 smoke/assertion이 필요하면 current browser contract에 직접 닿는 범위만 추가하세요.

검증 원칙:
- browser-visible contract가 바뀌므로 필요한 최소 browser verification을 포함하세요.
- 기본 후보:
  - `python3 -m py_compile app/web.py` if touched
  - focused `python3 -m unittest -v ...` if touched service logic
  - `make e2e-test`
  - `git diff --check`

dirty worktree 경고:
- 현재 worktree에는 unrelated dirty changes가 넓게 섞여 있습니다.
- unrelated 변경은 절대 되돌리거나 한 라운드에 섞지 마세요.

마무리:
- `/work` closeout을 남기세요.
- 응답은 한국어 존댓말로 작성하세요.
