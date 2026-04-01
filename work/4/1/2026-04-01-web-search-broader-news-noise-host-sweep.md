# 2026-04-01 web search broader news noise host sweep

## 변경 파일
- `tools/web_search.py`
- `tests/test_web_search_tool.py`

## 사용 skill
- 없음

## 변경 이유
- operator가 broader same-family sweep 1회를 허용 (host cluster 단위 bounded sweep).
- `core/source_policy.py`의 news_domain_hosts 80건 중 `tools/web_search.py`의 news boilerplate 필터에 미등록인 42건을 일괄 추가하여 정책 정합 완료.

## 핵심 변경
- `_looks_like_domain_specific_noise`의 `news_hosts` 튜플에 42건 일괄 추가:
  - IT/전문지: `etnews.com`, `bloter.net`
  - 독립/시사: `ohmynews.com`, `pressian.com`, `nocutnews.co.kr`, `news1.kr`
  - 지역신문 34건: `kyeonggi.com`, `sisafocus.co.kr`, `ikbc.co.kr`, `kado.net`, `ggilbo.com`, `idaegu.com`, `kyeongin.com`, `yeongnam.com`, `jemin.com`, `jeonmae.co.kr`, `gndomin.com`, `kwangju.co.kr`, `ksilbo.co.kr`, `imaeil.com`, `kookje.co.kr`, `jnilbo.com`, `jjan.kr`, `iusm.co.kr`, `mdilbo.com`, `idaebae.com`, `kbsm.net`, `incheonilbo.com`, `daejonilbo.com`, `kihoilbo.co.kr`, `kyeongbuk.co.kr`, `goodmorningcc.com`, `cctoday.co.kr`, `chungnamilbo.co.kr`, `daejeonilbo.com`, `joongdo.co.kr`, `dynews.co.kr`, `ccdailynews.com`, `jbnews.com`, `gjdream.com`, `jejunews.com`, `headlinejeju.co.kr`, `sisafocus.co.kr`
- 기존 exact-or-subdomain boundary 매칭 유지
- `core/source_policy.py`(80건)과 `tools/web_search.py`(80건) news host 목록이 완전 일치
- `tests/test_web_search_tool.py`에 `test_fetch_page_broader_news_host_sweep_boilerplate` 추가 (cluster별 대표 positive 13건 + negative 3건)

## 검증
- `python3 -m unittest -v tests.test_web_search_tool`: 14 tests, OK (0.028s)
- `git diff --check -- tools/web_search.py tests/test_web_search_tool.py`: 통과
- 정합성 확인: `core/source_policy.py` news_domain_hosts 80건 == `tools/web_search.py` news_hosts 80건 (완전 일치)

## 남은 리스크
- news host 목록이 두 파일에 중복 관리됨. 장기적으로 단일 source-of-truth로 통합하면 유지보수 부담이 줄어듦.
- dirty worktree가 여전히 넓음.
