import unittest
from unittest.mock import patch

from tools.web_search import WebSearchTool


class WebSearchToolTest(unittest.TestCase):
    def test_parse_duckduckgo_results_extracts_titles_urls_and_snippets(self) -> None:
        html = """
        <div class="result">
          <a class="result__a" href="https://example.com/wiki">체인소 맨 - 위키백과</a>
          <div class="result__snippet">체인소 맨은 일본의 다크 판타지 만화입니다.</div>
        </div>
        <div class="result">
          <a class="result__a" href="https://duckduckgo.com/l/?uddg=https%3A%2F%2Fexample.com%2Fanime">체인소맨 애니메이션</a>
          <div class="result__snippet">애니메이션과 원작 정보가 함께 정리된 페이지입니다.</div>
        </div>
        """
        tool = WebSearchTool()

        results = tool._parse_duckduckgo_results(html, max_results=5)

        self.assertEqual(len(results), 2)
        self.assertEqual(results[0].title, "체인소 맨 - 위키백과")
        self.assertEqual(results[0].url, "https://example.com/wiki")
        self.assertIn("다크 판타지 만화", results[0].snippet)
        self.assertEqual(results[1].url, "https://example.com/anime")

    def test_fetch_page_extracts_visible_text(self) -> None:
        html = """
        <html>
          <head>
            <title>아이유 최신 소식</title>
            <style>.hidden { display:none; }</style>
            <script>console.log('ignore');</script>
          </head>
          <body>
            <article>
              <h1>아이유 최신 소식</h1>
              <p>아이유의 새 앨범 일정과 최근 공연 소식을 정리했습니다.</p>
              <p>팬미팅 일정과 공개된 티저 정보도 함께 확인할 수 있습니다.</p>
            </article>
          </body>
        </html>
        """.encode("utf-8")

        class _FakeHeaders:
            def get(self, key: str, default=None):
                if key.lower() == "content-type":
                    return "text/html; charset=utf-8"
                return default

            def get_content_charset(self):
                return "utf-8"

        class _FakeResponse:
            headers = _FakeHeaders()

            def read(self):
                return html

            def __enter__(self):
                return self

            def __exit__(self, exc_type, exc, tb):
                return False

        tool = WebSearchTool()

        with patch("tools.web_search.urlopen", return_value=_FakeResponse()):
            page = tool.fetch_page(url="https://example.com/iu-news")

        self.assertEqual(page.title, "아이유 최신 소식")
        self.assertIn("새 앨범 일정", page.text)
        self.assertNotIn("console.log", page.text)
        self.assertNotIn("display:none", page.text)

    def test_fetch_page_normalizes_non_ascii_url_path_before_request(self) -> None:
        requested_urls: list[str] = []

        class _FakeHeaders:
            def get(self, key: str, default=None):
                if key.lower() == "content-type":
                    return "text/html; charset=utf-8"
                return default

            def get_content_charset(self):
                return "utf-8"

        class _FakeResponse:
            headers = _FakeHeaders()

            def read(self):
                return "<html><body><p>본문</p></body></html>".encode("utf-8")

            def __enter__(self):
                return self

            def __exit__(self, exc_type, exc, tb):
                return False

        def _capture_request(request, timeout=None):
            requested_urls.append(str(getattr(request, "full_url", "")))
            return _FakeResponse()

        tool = WebSearchTool()

        with patch("tools.web_search.urlopen", side_effect=_capture_request):
            page = tool.fetch_page(url="https://ko.wikipedia.org/wiki/이재용")

        self.assertEqual(page.title, "https://ko.wikipedia.org/wiki/이재용")
        self.assertTrue(requested_urls)
        self.assertIn("%EC%9D%B4%EC%9E%AC%EC%9A%A9", requested_urls[0])

    def test_fetch_page_filters_official_game_site_cta_and_footer_noise(self) -> None:
        html = """
        <html>
          <head><title>메이플스토리</title></head>
          <body>
            <main>
              <p>메이플스토리는 넥슨이 서비스하는 온라인 액션 RPG 게임이다.</p>
              <p>지금 바로 다운로드하고 함께 이용해 보세요!</p>
              <p>대표이사 강대현 · 김정욱 / 사업자등록번호 220-87-17483 / 전화 1588-7701</p>
            </main>
          </body>
        </html>
        """.encode("utf-8")

        class _FakeHeaders:
            def get(self, key: str, default=None):
                if key.lower() == "content-type":
                    return "text/html; charset=utf-8"
                return default

            def get_content_charset(self):
                return "utf-8"

        class _FakeResponse:
            headers = _FakeHeaders()

            def read(self):
                return html

            def __enter__(self):
                return self

            def __exit__(self, exc_type, exc, tb):
                return False

        tool = WebSearchTool()

        with patch("tools.web_search.urlopen", return_value=_FakeResponse()):
            page = tool.fetch_page(url="https://maplestory.nexon.com/Home/Main")

        self.assertIn("메이플스토리는 넥슨이 서비스하는 온라인 액션 RPG 게임이다.", page.text)
        self.assertNotIn("함께 이용해 보세요", page.text)
        self.assertNotIn("사업자등록번호", page.text)
        self.assertNotIn("1588-7701", page.text)

    def test_fetch_page_filters_game_portal_menu_noise(self) -> None:
        html = """
        <html>
          <head><title>붉은사막 - 네이버 게임</title></head>
          <body>
            <div>게시판 길드 친구 찾기 갤러리 공식 카페 동영상 스크린샷 팬아트</div>
            <article>
              <p>붉은사막은 펄어비스가 개발 중인 오픈월드 액션 어드벤처 게임이다.</p>
            </article>
          </body>
        </html>
        """.encode("utf-8")

        class _FakeHeaders:
            def get(self, key: str, default=None):
                if key.lower() == "content-type":
                    return "text/html; charset=utf-8"
                return default

            def get_content_charset(self):
                return "utf-8"

        class _FakeResponse:
            headers = _FakeHeaders()

            def read(self):
                return html

            def __enter__(self):
                return self

            def __exit__(self, exc_type, exc, tb):
                return False

        tool = WebSearchTool()

        with patch("tools.web_search.urlopen", return_value=_FakeResponse()):
            page = tool.fetch_page(url="https://game.naver.com/MapleStory")

        self.assertIn("붉은사막은 펄어비스가 개발 중인 오픈월드 액션 어드벤처 게임이다.", page.text)
        self.assertNotIn("게시판", page.text)
        self.assertNotIn("팬아트", page.text)

    def test_fetch_page_filters_wiki_metadata_noise(self) -> None:
        html = """
        <html>
          <head><title>붉은사막 - 나무위키</title></head>
          <body>
            <div>최근 수정 시각: 2026-03-26 12:00:00</div>
            <div>역링크 토론 편집 역사 ACL</div>
            <div>분류: 펄어비스 게임</div>
            <article>
              <p>붉은사막은 펄어비스가 개발 중인 오픈월드 액션 어드벤처 게임이다.</p>
            </article>
          </body>
        </html>
        """.encode("utf-8")

        class _FakeHeaders:
            def get(self, key: str, default=None):
                if key.lower() == "content-type":
                    return "text/html; charset=utf-8"
                return default

            def get_content_charset(self):
                return "utf-8"

        class _FakeResponse:
            headers = _FakeHeaders()

            def read(self):
                return html

            def __enter__(self):
                return self

            def __exit__(self, exc_type, exc, tb):
                return False

        tool = WebSearchTool()

        with patch("tools.web_search.urlopen", return_value=_FakeResponse()):
            page = tool.fetch_page(url="https://namu.wiki/w/%EB%B6%89%EC%9D%80%EC%82%AC%EB%A7%89")

        self.assertIn("붉은사막은 펄어비스가 개발 중인 오픈월드 액션 어드벤처 게임이다.", page.text)
        self.assertNotIn("최근 수정 시각", page.text)
        self.assertNotIn("역링크", page.text)
        self.assertNotIn("분류:", page.text)

    def test_fetch_page_filters_news_metadata_noise(self) -> None:
        html = """
        <html>
          <head><title>붉은사막 출시 일정</title></head>
          <body>
            <div>입력 2026.03.26 09:00 수정 2026.03.26 09:30</div>
            <div>김철수 기자</div>
            <article>
              <p>붉은사막은 펄어비스가 개발 중인 오픈월드 액션 어드벤처 게임으로 알려져 있다.</p>
            </article>
            <div>무단전재 및 재배포 금지</div>
          </body>
        </html>
        """.encode("utf-8")

        class _FakeHeaders:
            def get(self, key: str, default=None):
                if key.lower() == "content-type":
                    return "text/html; charset=utf-8"
                return default

            def get_content_charset(self):
                return "utf-8"

        class _FakeResponse:
            headers = _FakeHeaders()

            def read(self):
                return html

            def __enter__(self):
                return self

            def __exit__(self, exc_type, exc, tb):
                return False

        tool = WebSearchTool()

        with patch("tools.web_search.urlopen", return_value=_FakeResponse()):
            page = tool.fetch_page(url="https://sportsseoul.com/news/read/123456")

        self.assertIn("붉은사막은 펄어비스가 개발 중인 오픈월드 액션 어드벤처 게임으로 알려져 있다.", page.text)
        self.assertNotIn("입력 2026.03.26", page.text)
        self.assertNotIn("김철수 기자", page.text)
        self.assertNotIn("무단전재", page.text)

    def test_fetch_page_filters_blog_metadata_noise(self) -> None:
        html = """
        <html>
          <head><title>붉은사막 정리</title></head>
          <body>
            <div>본문 기타 기능</div>
            <div>카테고리 게임 / 태그 붉은사막</div>
            <article>
              <p>붉은사막은 펄어비스가 개발 중인 오픈월드 액션 어드벤처 게임으로 소개된다.</p>
            </article>
            <div>공감 댓글 공유하기</div>
          </body>
        </html>
        """.encode("utf-8")

        class _FakeHeaders:
            def get(self, key: str, default=None):
                if key.lower() == "content-type":
                    return "text/html; charset=utf-8"
                return default

            def get_content_charset(self):
                return "utf-8"

        class _FakeResponse:
            headers = _FakeHeaders()

            def read(self):
                return html

            def __enter__(self):
                return self

            def __exit__(self, exc_type, exc, tb):
                return False

        tool = WebSearchTool()

        with patch("tools.web_search.urlopen", return_value=_FakeResponse()):
            page = tool.fetch_page(url="https://example.tistory.com/123")

        self.assertIn("붉은사막은 펄어비스가 개발 중인 오픈월드 액션 어드벤처 게임으로 소개된다.", page.text)
        self.assertNotIn("본문 기타 기능", page.text)
        self.assertNotIn("카테고리", page.text)
        self.assertNotIn("공감", page.text)


    def test_fetch_page_news_noise_filter_exact_boundary(self) -> None:
        """news boilerplate 필터가 exact-or-subdomain boundary만 적용되는지 확인합니다.
        fake host(mychosun.com, foo-yna.co.kr, notmk.co.kr, news.google.com)에서는
        boilerplate가 제거되지 않아야 합니다."""
        html = """
        <html>
          <head><title>기준금리 속보</title></head>
          <body>
            <div>입력 2026.04.01 09:00</div>
            <div>김철수 기자</div>
            <article>
              <p>한국은행이 기준금리를 동결했다고 밝혔다.</p>
            </article>
            <div>무단전재 및 재배포 금지</div>
          </body>
        </html>
        """.encode("utf-8")

        class _FakeHeaders:
            def get(self, key: str, default=None):
                if key.lower() == "content-type":
                    return "text/html; charset=utf-8"
                return default

            def get_content_charset(self):
                return "utf-8"

        class _FakeResponse:
            headers = _FakeHeaders()

            def read(self):
                return html

            def __enter__(self):
                return self

            def __exit__(self, exc_type, exc, tb):
                return False

        tool = WebSearchTool()

        # positive: real news host → boilerplate 제거
        with patch("tools.web_search.urlopen", return_value=_FakeResponse()):
            page = tool.fetch_page(url="https://www.chosun.com/economy/2025")
        self.assertNotIn("무단전재", page.text)
        self.assertNotIn("김철수 기자", page.text)

        with patch("tools.web_search.urlopen", return_value=_FakeResponse()):
            page = tool.fetch_page(url="https://www.yna.co.kr/view/AKR20260401")
        self.assertNotIn("무단전재", page.text)

        with patch("tools.web_search.urlopen", return_value=_FakeResponse()):
            page = tool.fetch_page(url="https://www.mk.co.kr/economy/2025")
        self.assertNotIn("무단전재", page.text)

        # negative: fake host → boilerplate 유지 (제거되지 않음)
        with patch("tools.web_search.urlopen", return_value=_FakeResponse()):
            page = tool.fetch_page(url="https://mychosun.com/article/1")
        self.assertIn("무단전재", page.text)

        with patch("tools.web_search.urlopen", return_value=_FakeResponse()):
            page = tool.fetch_page(url="https://foo-yna.co.kr/article/1")
        self.assertIn("무단전재", page.text)

        with patch("tools.web_search.urlopen", return_value=_FakeResponse()):
            page = tool.fetch_page(url="https://notmk.co.kr/article/1")
        self.assertIn("무단전재", page.text)

        with patch("tools.web_search.urlopen", return_value=_FakeResponse()):
            page = tool.fetch_page(url="https://news.google.com/articles/1")
        self.assertIn("무단전재", page.text)

    def test_fetch_page_portal_news_host_boilerplate_boundary(self) -> None:
        """portal news host 5건은 boilerplate 제거 대상이고,
        news.google.com, blog.naver.com, cafe.daum.net은 대상이 아님을 잠급니다."""
        html = """
        <html>
          <head><title>기준금리 속보</title></head>
          <body>
            <div>입력 2026.04.01 09:00</div>
            <div>김철수 기자</div>
            <article>
              <p>한국은행이 기준금리를 동결했다고 밝혔다.</p>
            </article>
            <div>무단전재 및 재배포 금지</div>
          </body>
        </html>
        """.encode("utf-8")

        class _FakeHeaders:
            def get(self, key: str, default=None):
                if key.lower() == "content-type":
                    return "text/html; charset=utf-8"
                return default

            def get_content_charset(self):
                return "utf-8"

        class _FakeResponse:
            headers = _FakeHeaders()

            def read(self):
                return html

            def __enter__(self):
                return self

            def __exit__(self, exc_type, exc, tb):
                return False

        tool = WebSearchTool()

        # positive: portal news host → boilerplate 제거
        for url in (
            "https://news.naver.com/main/read.naver?oid=001&aid=0000001",
            "https://v.daum.net/v/20260401120000001",
            "https://news.daum.net/v/20260401120000001",
            "https://news.nate.com/view/20260401n00123",
            "https://news.zum.com/articles/97600001",
        ):
            with patch("tools.web_search.urlopen", return_value=_FakeResponse()):
                page = tool.fetch_page(url=url)
            self.assertNotIn("무단전재", page.text, f"boilerplate should be removed for {url}")

        # negative: non-news portal/community host → boilerplate 유지
        for url in (
            "https://news.google.com/articles/1",
            "https://blog.naver.com/example/1",
            "https://cafe.daum.net/example/1",
        ):
            with patch("tools.web_search.urlopen", return_value=_FakeResponse()):
                page = tool.fetch_page(url=url)
            self.assertIn("무단전재", page.text, f"boilerplate should NOT be removed for {url}")

    def test_fetch_page_national_news_host_boilerplate_boundary(self) -> None:
        """national-news host 11건은 boilerplate 제거 대상이고,
        news.google.com, blog.naver.com, cafe.daum.net은 대상이 아님을 잠급니다."""
        html = """
        <html>
          <head><title>기준금리 속보</title></head>
          <body>
            <div>입력 2026.04.01 09:00</div>
            <div>김철수 기자</div>
            <article>
              <p>한국은행이 기준금리를 동결했다고 밝혔다.</p>
            </article>
            <div>무단전재 및 재배포 금지</div>
          </body>
        </html>
        """.encode("utf-8")

        class _FakeHeaders:
            def get(self, key: str, default=None):
                if key.lower() == "content-type":
                    return "text/html; charset=utf-8"
                return default

            def get_content_charset(self):
                return "utf-8"

        class _FakeResponse:
            headers = _FakeHeaders()

            def read(self):
                return html

            def __enter__(self):
                return self

            def __exit__(self, exc_type, exc, tb):
                return False

        tool = WebSearchTool()

        # positive: national news host → boilerplate 제거
        for url in (
            "https://www.hankyung.com/economy/2025",
            "https://www.edaily.co.kr/news/2025",
            "https://www.etoday.co.kr/news/2025",
            "https://news.heraldcorp.com/view/2025",
            "https://zdnet.co.kr/view/2025",
            "https://www.dt.co.kr/contents/2025",
            "https://www.seoul.co.kr/news/2025",
            "https://biz.newdaily.co.kr/news/2025",
            "https://www.moneytoday.co.kr/news/2025",
            "https://www.segye.com/newsView/202604010001",
            "https://www.newsis.com/view/NISX20260401_0001",
        ):
            with patch("tools.web_search.urlopen", return_value=_FakeResponse()):
                page = tool.fetch_page(url=url)
            self.assertNotIn("무단전재", page.text, f"boilerplate should be removed for {url}")

        # negative: non-news host → boilerplate 유지
        for url in (
            "https://news.google.com/articles/1",
            "https://blog.naver.com/example/1",
            "https://cafe.daum.net/example/1",
        ):
            with patch("tools.web_search.urlopen", return_value=_FakeResponse()):
                page = tool.fetch_page(url=url)
            self.assertIn("무단전재", page.text, f"boilerplate should NOT be removed for {url}")

    def test_fetch_page_broadcast_news_host_boilerplate_boundary(self) -> None:
        """broadcast/newsroom host 7건은 boilerplate 제거 대상이고,
        news.google.com, blog.naver.com, cafe.daum.net은 대상이 아님을 잠급니다."""
        html = """
        <html>
          <head><title>기준금리 속보</title></head>
          <body>
            <div>입력 2026.04.01 09:00</div>
            <div>김철수 기자</div>
            <article>
              <p>한국은행이 기준금리를 동결했다고 밝혔다.</p>
            </article>
            <div>무단전재 및 재배포 금지</div>
          </body>
        </html>
        """.encode("utf-8")

        class _FakeHeaders:
            def get(self, key: str, default=None):
                if key.lower() == "content-type":
                    return "text/html; charset=utf-8"
                return default

            def get_content_charset(self):
                return "utf-8"

        class _FakeResponse:
            headers = _FakeHeaders()

            def read(self):
                return html

            def __enter__(self):
                return self

            def __exit__(self, exc_type, exc, tb):
                return False

        tool = WebSearchTool()

        # positive: broadcast news host → boilerplate 제거
        for url in (
            "https://www.mbn.co.kr/news/economy/5000001",
            "https://news.sbs.co.kr/news/endPage.do?news_id=N1001",
            "https://news.kbs.co.kr/news/pc/view/view.do?ncd=8000001",
            "https://www.ytn.co.kr/_ln/0102_202604010001",
            "https://news.jtbc.co.kr/article/article.aspx?news_id=NB12100001",
            "https://www.ichannela.com/news/main/news_detail.do?publishId=000000001",
            "https://news.tvchosun.com/site/data/html_dir/2026/04/01/2026040100001.html",
        ):
            with patch("tools.web_search.urlopen", return_value=_FakeResponse()):
                page = tool.fetch_page(url=url)
            self.assertNotIn("무단전재", page.text, f"boilerplate should be removed for {url}")

        # negative: non-news host → boilerplate 유지
        for url in (
            "https://news.google.com/articles/1",
            "https://blog.naver.com/example/1",
            "https://cafe.daum.net/example/1",
        ):
            with patch("tools.web_search.urlopen", return_value=_FakeResponse()):
                page = tool.fetch_page(url=url)
            self.assertIn("무단전재", page.text, f"boilerplate should NOT be removed for {url}")

    def test_fetch_page_sisajournal_boilerplate_boundary(self) -> None:
        """sisajournal.com은 boilerplate 제거 대상이고,
        news.google.com, blog.naver.com, cafe.daum.net은 대상이 아님을 잠급니다."""
        html = """
        <html>
          <head><title>기준금리 속보</title></head>
          <body>
            <div>입력 2026.04.01 09:00</div>
            <div>김철수 기자</div>
            <article>
              <p>한국은행이 기준금리를 동결했다고 밝혔다.</p>
            </article>
            <div>무단전재 및 재배포 금지</div>
          </body>
        </html>
        """.encode("utf-8")

        class _FakeHeaders:
            def get(self, key: str, default=None):
                if key.lower() == "content-type":
                    return "text/html; charset=utf-8"
                return default

            def get_content_charset(self):
                return "utf-8"

        class _FakeResponse:
            headers = _FakeHeaders()

            def read(self):
                return html

            def __enter__(self):
                return self

            def __exit__(self, exc_type, exc, tb):
                return False

        tool = WebSearchTool()

        # positive: sisajournal.com → boilerplate 제거
        with patch("tools.web_search.urlopen", return_value=_FakeResponse()):
            page = tool.fetch_page(url="https://www.sisajournal.com/news/articleView.html?idxno=123456")
        self.assertNotIn("무단전재", page.text)

        # negative: non-news host → boilerplate 유지
        for url in (
            "https://news.google.com/articles/1",
            "https://blog.naver.com/example/1",
            "https://cafe.daum.net/example/1",
        ):
            with patch("tools.web_search.urlopen", return_value=_FakeResponse()):
                page = tool.fetch_page(url=url)
            self.assertIn("무단전재", page.text, f"boilerplate should NOT be removed for {url}")

    def test_fetch_page_broader_news_host_sweep_boilerplate(self) -> None:
        """broader sweep: IT전문지, 독립매체, 지역신문 대표 host들이
        boilerplate 제거 대상인지 확인합니다."""
        html = """
        <html>
          <head><title>기준금리 속보</title></head>
          <body>
            <div>입력 2026.04.01 09:00</div>
            <div>김철수 기자</div>
            <article>
              <p>한국은행이 기준금리를 동결했다고 밝혔다.</p>
            </article>
            <div>무단전재 및 재배포 금지</div>
          </body>
        </html>
        """.encode("utf-8")

        class _FakeHeaders:
            def get(self, key: str, default=None):
                if key.lower() == "content-type":
                    return "text/html; charset=utf-8"
                return default

            def get_content_charset(self):
                return "utf-8"

        class _FakeResponse:
            headers = _FakeHeaders()

            def read(self):
                return html

            def __enter__(self):
                return self

            def __exit__(self, exc_type, exc, tb):
                return False

        tool = WebSearchTool()

        # positive: cluster별 대표 host → boilerplate 제거
        for url in (
            # IT/전문지
            "https://www.etnews.com/20260401000001",
            "https://www.bloter.net/news/articleView.html?idxno=123456",
            # 독립/시사
            "https://www.ohmynews.com/NWS_Web/View/at_pg.aspx?CNTN_CD=A0001",
            "https://www.pressian.com/pages/articles/2026040100001",
            "https://www.nocutnews.co.kr/news/6100001",
            "https://www.news1.kr/articles/?5000001",
            # 지역신문 대표
            "https://www.kyeonggi.com/article/1",
            "https://www.kado.net/news/articleView.html?idxno=123456",
            "https://www.yeongnam.com/web/view.php?key=202604010001",
            "https://www.kookje.co.kr/news2011/asp/newsbody.asp?code=0300&key=1",
            "https://www.jjan.kr/article/20260401500001",
            "https://www.incheonilbo.com/news/articleView.html?idxno=123456",
            "https://www.jejunews.com/news/articleView.html?idxno=123456",
        ):
            with patch("tools.web_search.urlopen", return_value=_FakeResponse()):
                page = tool.fetch_page(url=url)
            self.assertNotIn("무단전재", page.text, f"boilerplate should be removed for {url}")

        # negative: non-news host → boilerplate 유지
        for url in (
            "https://news.google.com/articles/1",
            "https://blog.naver.com/example/1",
            "https://cafe.daum.net/example/1",
        ):
            with patch("tools.web_search.urlopen", return_value=_FakeResponse()):
                page = tool.fetch_page(url=url)
            self.assertIn("무단전재", page.text, f"boilerplate should NOT be removed for {url}")


if __name__ == "__main__":
    unittest.main()
