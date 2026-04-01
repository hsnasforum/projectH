# 2026-04-01 broader news-domain sweep

## 변경 파일
- `core/source_policy.py`
- `core/agent_loop.py`
- `tests/test_source_policy.py`
- `tests/test_web_app.py`

## 사용 skill
- 없음

## 변경 이유
- `.pipeline/codex_feedback.md`가 `STATUS: needs_operator`로, 다음 same-family residual 1건을 특정할 수 없어 자동화를 멈춤.
- operator가 broader same-family news-domain sweep 1회를 허용.
- 아직 `general`로 분류되던 한국 주요 지역신문, 통신사, 방송사, 전문지 도메인 21건을 일괄 추가.

## 핵심 변경
- `classify_source_type`와 `_classify_web_source_kind` news_host_hints에 21개 도메인 일괄 추가:
  - 지역신문: `dynews.co.kr`, `ccdailynews.com`, `jbnews.com`, `gjdream.com`, `jejunews.com`, `headlinejeju.co.kr`
  - 독립/시사매체: `ohmynews.com`, `pressian.com`, `nocutnews.co.kr`
  - 통신사: `newsis.com`, `news1.kr`
  - 방송사: `mbn.co.kr`, `sbs.co.kr`, `kbs.co.kr`, `ytn.co.kr`, `jtbc.co.kr`, `ichannela.com`, `tvchosun.com`
  - IT/전문지: `etnews.com`, `bloter.net`
- `test_classify_source_type_maps_known_domains`에 21건 전체 assertion 추가
- `test_handle_chat_latest_update_newsis_mk_noisy_community_badge_contract` 추가 (대표 badge contract 1건)

## 검증
- `python3 -m unittest -v tests.test_source_policy tests.test_web_app`: 172 tests, OK (3.028s)
- `git diff --check -- core/source_policy.py core/agent_loop.py tests/test_source_policy.py tests/test_web_app.py`: 통과

## 남은 리스크
- 이번 sweep은 operator 승인 아래 주요 도메인을 일괄 추가. 장기적으로 매우 작은 지역지는 계속 `general`로 남을 수 있음.
- dirty worktree가 여전히 넓음.
